import orthanc
import json
import zipfile
import os
import tempfile
import threading
import time
from typing import List, Dict
from boto3 import client as S3Client
from local_storage_interface import LocalStorageInterface
from custom_data import CustomData



# This class is in charge of compressing and moving series between the local storage
# and S3.
class LocalToS3ZipManager:

    # This class is only used to make sure we do not download twice the same series at the 
    # same time.  The ZipRetrieval is destructed at the end of the download phase once the
    # files are stored in the local storage -> the files are not locked in the local storage
    # but they are referenced in a LRU (TODO).
    class ZipRetrieval:

        series_id: str
        _condition: threading.Condition
        _ref_count: int
        _manager: 'LocalToS3ZipManager'
        _downloaded: bool

        def __init__(self, series_id: str, manager: 'LocalToS3ZipManager'):
            self.series_id = series_id
            self._condition = threading.Condition()
            self._ref_count = 0
            self._manager = manager
            self._downloaded = False

        def __enter__(self):
            orthanc.LogInfo(f"Entering ZipRetrieval: {self.series_id}")
            self._ref_count += 1
            self._condition.__enter__()
            orthanc.LogInfo(f"Entered ZipRetrieval: {self.series_id}")

        def __exit__(self, exc_type, exc_val, exc_tb):
            orthanc.LogInfo(f"Exiting ZipRetrieval: {self.series_id}")
            self._ref_count -= 1
            self._condition.__exit__(exc_type, exc_val, exc_tb)
            if self._ref_count == 0:
                orthanc.LogInfo(f"Removing ZipRetrieval: {self.series_id}")
                self._manager._discard_zip_retrieval(self.series_id)
            orthanc.LogInfo(f"Exited ZipRetrieval: {self.series_id}")

        @property
        def downloaded(self):
            return self._downloaded

        def set_downloaded(self):
            orthanc.LogInfo(f"Set Downloaded: {self.series_id}")
            self._downloaded = True
            self._condition.notify_all()
            orthanc.LogInfo(f"Set Downloaded: {self.series_id}, done")

        def wait_downloaded(self):
            orthanc.LogInfo(f"Waiting Downloaded: {self.series_id}")
            while not self._downloaded:
                self._condition.wait()
            orthanc.LogInfo(f"Waiting Downloaded: {self.series_id}, done")

    _s3_client: S3Client
    _local_storage: LocalStorageInterface
    _bucket_name: str
    _s3_zip_retrievals: Dict[str, ZipRetrieval]
    _s3_zip_retrievals_lock: threading.Lock
    _copy_thread: threading.Thread
    _threads_should_stop: bool

    def __init__(self, s3_client: S3Client, bucket_name: str, local_storage: LocalStorageInterface):
        self._s3_client = s3_client
        self._bucket_name = bucket_name
        self._local_storage = local_storage
        self._s3_zip_retrievals = {}
        self._s3_zip_retrievals_lock = threading.Lock()
        self._threads_should_stop = False
        self._copy_thread = threading.Thread(target=self._copy_thread_worker)

    def start(self):
        self._copy_thread.start()

    def stop(self):
        self._threads_should_stop = True
        self._copy_thread.join()

    def _get_series_s3_key(self, series_id: str) -> str:
        return f"{series_id}.zip"

    def schedule_copy_series_to_s3(self, series_id: str):
        orthanc.LogInfo(f"LocalToS3ZipManager: scheduling move of series {series_id} to S3")
        orthanc.EnqueueValue("series-to-copy", series_id.encode('utf-8'))

    def _copy_thread_worker(self):
        orthanc.SetCurrentThreadName("S3-COPY-THREAD")
        orthanc.LogInfo(f"LocalToS3ZipManager: started copy thread")

        while not self._threads_should_stop:
            bseries_id, value_id = orthanc.ReserveQueueValue("series-to-copy", orthanc.QueueOrigin.FRONT, 600)

            if bseries_id is None:
                time.sleep(1)
            else:
                try:
                    series_id=bseries_id.decode('utf-8')
                    self.copy_series_to_s3(series_id=series_id)
                except Exception as e:
                    orthanc.LogWarning(f"LocalToS3ZipManager: failed to move series {series_id} to S3: {str(e)}")
                    # TODO: identify if this is a "permanent failure".  In this case, no need to repost the message + handle max retries
                    orthanc.EnqueueValue("series-to-copy", bseries_id)

                orthanc.AcknowledgeQueueValue("series-to-copy", value_id)

        orthanc.LogInfo(f"LocalToS3ZipManager: stopping copy thread")

    def copy_series_to_s3(self, series_id: str):
        orthanc.LogInfo(f"LocalToS3ZipManager: moving series {series_id} to S3")

        # list all instances attachments
        attachments_uuids = self._get_instances_attachments(series_id=series_id)
        local_series_folder = None

        # let's zip them in a temp file and upload it to S3.
        with tempfile.NamedTemporaryFile(delete=True, suffix=".zip") as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, "w") as zipf:
                for a_uuid in attachments_uuids:
                    if not local_series_folder: # they all share the same folder
                        local_series_folder = CustomData.from_orthanc_attachment(a_uuid).local_series_folder
                    content = self._local_storage.read_file(uuid=a_uuid, 
                                                            local_series_folder=local_series_folder)
                    zipf.writestr(a_uuid, content)

            # Upload to S3
            s3_key = self._get_series_s3_key(series_id)
            self._s3_client.upload_file(tmp_zip.name, self._bucket_name, s3_key)

            # Update the custom data to notify that the file is now stored in a zip in S3
            s3_custom_data = CustomData(storage=CustomData.Storage.S3_ZIP,
                                        local_series_folder=local_series_folder,
                                        s3_zip_key=s3_key).to_binary()
            
            for a_uuid in attachments_uuids:
                orthanc.SetAttachmentCustomData(a_uuid, s3_custom_data)

            # At this point, the local storage does not need to keep the files stored locally but there is no need to notify it.
            # In the best scenario, the files will still be stored locally at the time we need it.

        orthanc.LogInfo(f"LocalToS3ZipManager: moved series {series_id} to S3")

    def _discard_zip_retrieval(self, series_id: str):
        with self._s3_zip_retrievals_lock:
            del self._s3_zip_retrievals[series_id]

    def retrieve_zip_from_s3(self, s3_zip_key: str, local_series_folder: str):
        # make sure we do not retrieve the same file multiple times at the same time
        with self._s3_zip_retrievals_lock:  # global lock to safely manipulate the retrieval dict
            if s3_zip_key not in self._s3_zip_retrievals:
                self._s3_zip_retrievals[s3_zip_key] = LocalToS3ZipManager.ZipRetrieval(s3_zip_key, manager=self)
            zip_retrieval = self._s3_zip_retrievals[s3_zip_key]

        with zip_retrieval: # the first thread to get here keeps the condition "locked" during the zip retrieval
            if not zip_retrieval.downloaded:
                self._retrieve_zip_from_s3(s3_zip_key, local_series_folder)
                zip_retrieval.set_downloaded()
            else:
                zip_retrieval.wait_downloaded()

            

    def _retrieve_zip_from_s3(self, s3_zip_key: str, local_series_folder: str):
        orthanc.LogInfo(f"Retrieving zip from s3: {s3_zip_key}")
        with tempfile.NamedTemporaryFile(delete=True, suffix=".zip") as tmp_zip:
            self._s3_client.download_file(self._bucket_name,
                                          s3_zip_key, 
                                          tmp_zip.name)
            
            with zipfile.ZipFile(tmp_zip.name, 'r') as zipf:
                for file_info in zipf.infolist():
                    with zipf.open(file_info) as f:
                        self._local_storage.write_file(uuid=file_info.filename,
                                                       local_series_folder=local_series_folder,
                                                       content=f.read())
        orthanc.LogInfo(f"Retrieving zip from s3: {s3_zip_key}, done")


    def _get_instances_attachments(self, series_id: str) -> List[str]:
        payload = {
            "Level": "Instance",
            "Query": {},
            "ResponseContent": ["Attachments"],
            "ParentSeries": series_id 
        }
        instances_info = json.loads(orthanc.RestApiPost("/tools/find", json.dumps(payload).encode('utf-8')))
        attachments_uuids = []
        # print(instances_info)
        for i in instances_info:
            attachments_uuids.append(i["Attachments"][0]["Uuid"])  # TODO: handle attachments other than DICOM ('ContentType': 1)

        # print(attachments_uuids)

        return attachments_uuids
