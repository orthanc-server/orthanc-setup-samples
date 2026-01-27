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

# This class is in charge of compressing and moving series between the local storage
# and S3.
class LocalToS3ZipManager:

    _s3_client: S3Client
    _local_storage: LocalStorageInterface
    _bucket_name: str
    # _s3_zips_being_retrieved: List[str]
    _s3_zips_being_retrieved_conditions: Dict[str, threading.Condition]
    _s3_zips_being_retrieved_locks: Dict[str, threading.Lock]
    _s3_zips_being_retrieved_meta_lock: threading.Lock
    _s3_zips_download: List[str]
    _copy_thread: threading.Thread
    _threads_should_stop: bool

    def __init__(self, s3_client: S3Client, bucket_name: str, local_storage: LocalStorageInterface):
        self._s3_client = s3_client
        self._bucket_name = bucket_name
        self._local_storage = local_storage
        # self._s3_zips_being_retrieved = []
        self._s3_zips_being_retrieved_conditions = {}
        self._s3_zips_being_retrieved_locks = {}
        self._s3_zips_being_retrieved_meta_lock = threading.Lock()
        self._s3_zips_download = []
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
                    # TODO: identify if this is a "permanent failure".  In this case, no need to repost the message
                    orthanc.EnqueueValue("series-to-copy", bseries_id)

                orthanc.AcknowledgeQueueValue("series-to-copy", value_id)

        orthanc.LogInfo(f"LocalToS3ZipManager: stopping copy thread")

    def copy_series_to_s3(self, series_id: str):
        orthanc.LogInfo(f"LocalToS3ZipManager: moving series {series_id} to S3")

        # list all instances attachments
        attachments_uuids = self._get_instances_attachments(series_id=series_id)
        
        # let's zip them in a temp file and upload it to S3.
        with tempfile.NamedTemporaryFile(delete=True, suffix=".zip") as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, "w") as zipf:
                for a_uuid in attachments_uuids:
                    content = self._local_storage.read_file(uuid=a_uuid)
                    zipf.writestr(a_uuid, content)

            # Upload to S3
            s3_key = self._get_series_s3_key(series_id)
            self._s3_client.upload_file(tmp_zip.name, self._bucket_name, s3_key)

            # Update the custom data to notify that the file is now stored in a zip in S3
            custom_data_json = {
                "s3-zip-key": s3_key
            }
            custom_data_binary = json.dumps(custom_data_json).encode('utf-8')
            for a_uuid in attachments_uuids:
                orthanc.SetAttachmentCustomData(a_uuid, custom_data_binary)

            # At this point, the local storage does not need to keep the files stored locally but there is no need to notify it.
            # In the best scenario, the files will still be stored locally at the time we need it.

        orthanc.LogInfo(f"LocalToS3ZipManager: moved series {series_id} to S3")

    def retrieve_zip_from_s3(self, s3_zip_key: str):

        # make sure we do not retrieve the same file multiple times at the same time
        with self._s3_zips_being_retrieved_meta_lock:  # global lock to safely manipulate per-file conditions
            if s3_zip_key not in self._s3_zips_being_retrieved_conditions:
                self._s3_zips_being_retrieved_conditions[s3_zip_key] = threading.Condition()
            condition = self._s3_zips_being_retrieved_conditions[s3_zip_key]

        with condition: # the first thread to get here keeps the condition "locked" during the zip retrieval
            if s3_zip_key not in self._s3_zips_download:
                self._retrieve_zip_from_s3(s3_zip_key)
                self._s3_zips_download.append(s3_zip_key)   # TODO: at some point, when the we need to remove ids from this list + remove the conditions
                condition.notify_all() # notify all waiting threads
            else:
                # wait until the first thread has finished downloading the zip
                while s3_zip_key not in self._s3_zips_download:
                    condition.wait()
            

    def _retrieve_zip_from_s3(self, s3_zip_key: str):
        with tempfile.NamedTemporaryFile(delete=True, suffix=".zip") as tmp_zip:
            self._s3_client.download_file(self._bucket_name,
                                          s3_zip_key, 
                                          tmp_zip.name)
            
            with zipfile.ZipFile(tmp_zip.name, 'r') as zipf:
                for file_info in zipf.infolist():
                    with zipf.open(file_info) as f:
                        self._local_storage.write_file(uuid=file_info.filename,
                                                       content=f.read())


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
