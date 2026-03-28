import orthanc
import json
import zipfile
import os
import tempfile
import threading
import time
from typing import List, Dict, Optional
from boto3 import client as S3Client
from local_storage_interface import LocalStorageInterface
from uncommitted_series_handler import UncommittedSeriesHandler
from custom_data import CustomData
from s3zip_logging import get_logger

logger = get_logger(__name__)


class SeriesS3Info:

    series_id: str
    is_stored_in_s3: bool = False
    s3_zip_key: str = None

    def __init__(self, series_id: str):
        self.series_id = series_id


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
            logger.debug("ZipRetrieval created", s3_zip_key=series_id)

        def __enter__(self):
            logger.debug("ZipRetrieval entering (acquiring condition)",
                         s3_zip_key=self.series_id,
                         ref_count=self._ref_count + 1)
            self._ref_count += 1
            self._condition.__enter__()
            logger.debug("ZipRetrieval entered (condition acquired)",
                         s3_zip_key=self.series_id,
                         ref_count=self._ref_count)

        def __exit__(self, exc_type, exc_val, exc_tb):
            logger.debug("ZipRetrieval exiting",
                         s3_zip_key=self.series_id,
                         ref_count=self._ref_count)
            self._ref_count -= 1
            self._condition.__exit__(exc_type, exc_val, exc_tb)
            if self._ref_count == 0:
                logger.debug("ZipRetrieval ref_count reached 0, discarding",
                             s3_zip_key=self.series_id)
                self._manager._discard_zip_retrieval(self.series_id)
            logger.debug("ZipRetrieval exited",
                         s3_zip_key=self.series_id,
                         ref_count=self._ref_count)

        @property
        def downloaded(self):
            return self._downloaded

        def set_downloaded(self):
            logger.debug("ZipRetrieval set_downloaded, notifying waiters",
                         s3_zip_key=self.series_id)
            self._downloaded = True
            self._condition.notify_all()

        def wait_downloaded(self):
            logger.debug("ZipRetrieval waiting for download to complete",
                         s3_zip_key=self.series_id)
            while not self._downloaded:
                self._condition.wait()
            logger.debug("ZipRetrieval download wait completed",
                         s3_zip_key=self.series_id)

    _s3_client: S3Client
    _local_storage: LocalStorageInterface
    _uncommitted_series_handler: UncommittedSeriesHandler
    _bucket_name: str
    _s3_zip_retrievals: Dict[str, ZipRetrieval]
    _s3_zip_retrievals_lock: threading.Lock
    _copy_thread: threading.Thread
    _threads_should_stop: bool
    _zip_compression: int

    def __init__(self, s3_client: S3Client, bucket_name: str, local_storage: LocalStorageInterface, enable_compression: bool, uncommitted_series_handler: UncommittedSeriesHandler, key_prefix: str = ""):
        self._s3_client = s3_client
        self._bucket_name = bucket_name
        self._local_storage = local_storage
        self._uncommitted_series_handler = uncommitted_series_handler
        self._key_prefix = key_prefix.strip('/')
        if enable_compression:
            self._zip_compression = zipfile.ZIP_DEFLATED
        else:
            self._zip_compression = zipfile.ZIP_STORED
        self._s3_zip_retrievals = {}
        self._s3_zip_retrievals_lock = threading.Lock()
        self._threads_should_stop = False
        self._copy_thread = threading.Thread(target=self._copy_thread_worker)

        compression_name = "ZIP_DEFLATED" if enable_compression else "ZIP_STORED"
        logger.debug("LocalToS3ZipManager initialized",
                     bucket=bucket_name,
                     compression=compression_name,
                     key_prefix=self._key_prefix or "<none>")


    def start(self):
        logger.info("S3 copy thread starting")
        self._copy_thread.start()


    def stop(self):
        logger.info("S3 copy thread stopping")
        self._threads_should_stop = True
        self._copy_thread.join()
        logger.info("S3 copy thread stopped")


    def _get_series_s3_key(self, series_id: str) -> str:
        if self._key_prefix:
            return f"{self._key_prefix}/{series_id}.zip"
        return f"{series_id}.zip"


    def schedule_copy_series_to_s3(self, series_id: str):
        logger.debug("enqueuing series for S3 copy", series_id=series_id)
        logger.debug("calling orthanc.EnqueueValue()", series_id=series_id)
        orthanc.EnqueueValue("series-to-copy", series_id.encode('utf-8'))
        logger.debug("orthanc.EnqueueValue() returned", series_id=series_id)
        logger.debug("series enqueued for S3 copy", series_id=series_id)


    def _copy_thread_worker(self):
        orthanc.SetCurrentThreadName("S3-COPY-THREAD")
        logger.info("S3 copy thread started")

        while not self._threads_should_stop:
            logger.debug("calling orthanc.ReserveQueueValue(series-to-copy)")
            bseries_id, value_id = orthanc.ReserveQueueValue("series-to-copy", orthanc.QueueOrigin.FRONT, 600)
            logger.debug("orthanc.ReserveQueueValue() returned",
                         got_item=bseries_id is not None,
                         value_id=str(value_id) if value_id is not None else "<none>")

            if bseries_id is None:
                logger.debug("no series in copy queue, sleeping")
                time.sleep(1)
            else:
                series_id = bseries_id.decode('utf-8')
                logger.debug("dequeued series for S3 copy",
                             series_id=series_id,
                             value_id=str(value_id))
                logger.info("starting copy_series_to_s3", series_id=series_id)
                try:
                    self.copy_series_to_s3(series_id=series_id)
                except Exception as e:
                    logger.warning("failed to copy series to S3, re-enqueuing",
                                   series_id=series_id,
                                   error=str(e))
                    # TODO: identify if this is a "permanent failure".  In this case, no need to repost the message + handle max retries
                    logger.debug("re-enqueuing failed series via orthanc.EnqueueValue()", series_id=series_id)
                    orthanc.EnqueueValue("series-to-copy", bseries_id)
                    logger.debug("orthanc.EnqueueValue() returned after re-enqueue", series_id=series_id)

                logger.debug("calling orthanc.AcknowledgeQueueValue()", series_id=series_id, value_id=str(value_id))
                orthanc.AcknowledgeQueueValue("series-to-copy", value_id)
                logger.debug("orthanc.AcknowledgeQueueValue() returned", series_id=series_id)
                logger.info("copy_series_to_s3 cycle complete", series_id=series_id)

        logger.info("S3 copy thread exiting")


    def copy_series_to_s3(self, series_id: str):
        logger.info("series copy to S3 starting", series_id=series_id)
        t0 = time.monotonic()

        # list all instances attachments
        attachments_uuids = self._get_instances_attachments(series_id=series_id)
        local_series_folder = None

        logger.debug("collected instance attachments for series",
                     series_id=series_id,
                     attachment_count=len(attachments_uuids))

        total_uncompressed_bytes = 0

        # let's zip them in a temp file and upload it to S3.
        with tempfile.NamedTemporaryFile(delete=True, suffix=".zip") as tmp_zip:
            logger.debug("building zip archive",
                         series_id=series_id,
                         tmp_path=tmp_zip.name,
                         attachment_count=len(attachments_uuids))

            with zipfile.ZipFile(tmp_zip.name, "w", compression=self._zip_compression) as zipf:
                for idx, a_uuid in enumerate(attachments_uuids):
                    if not local_series_folder: # they all share the same folder
                        local_series_folder = CustomData.from_orthanc_attachment(a_uuid).local_series_folder
                        logger.debug("resolved local_series_folder from first attachment",
                                     series_id=series_id,
                                     local_series_folder=local_series_folder)
                    content = self._local_storage.read_file(uuid=a_uuid,
                                                            local_series_folder=local_series_folder)
                    total_uncompressed_bytes += len(content)
                    logger.debug("adding attachment to zip",
                                 series_id=series_id,
                                 uuid=a_uuid,
                                 index=idx,
                                 size_bytes=len(content))
                    zipf.writestr(a_uuid, content)
                    logger.debug("attachment added to zip",
                                 series_id=series_id,
                                 uuid=a_uuid,
                                 index=idx)

            t_zip_done = time.monotonic()
            zip_size_bytes = os.path.getsize(tmp_zip.name)

            logger.info("zip archive built",
                        series_id=series_id,
                        attachment_count=len(attachments_uuids),
                        zip_size_bytes=zip_size_bytes,
                        uncompressed_bytes=total_uncompressed_bytes,
                        zip_build_ms=int((t_zip_done - t0) * 1000))

            # Upload to S3
            s3_key = self._get_series_s3_key(series_id)
            logger.info("uploading zip to S3",
                        series_id=series_id,
                        s3_key=s3_key,
                        bucket=self._bucket_name,
                        zip_size_bytes=zip_size_bytes,
                        uncompressed_bytes=total_uncompressed_bytes)
            logger.debug("calling s3_client.upload_file()",
                         series_id=series_id,
                         s3_key=s3_key,
                         bucket=self._bucket_name)

            self._s3_client.upload_file(tmp_zip.name, self._bucket_name, s3_key)

            t_upload_done = time.monotonic()
            logger.debug("s3_client.upload_file() returned",
                         series_id=series_id,
                         s3_key=s3_key)
            logger.info("zip uploaded to S3",
                        series_id=series_id,
                        s3_key=s3_key,
                        bucket=self._bucket_name,
                        zip_size_bytes=zip_size_bytes,
                        upload_ms=int((t_upload_done - t_zip_done) * 1000))

            # Update the custom data to notify that the file is now stored in a zip in S3
            s3_custom_data = CustomData(storage=CustomData.Storage.S3_ZIP,
                                        local_series_folder=local_series_folder,
                                        s3_zip_key=s3_key).to_binary()

            logger.info("starting SetAttachmentCustomData loop",
                        series_id=series_id,
                        attachment_count=len(attachments_uuids),
                        s3_key=s3_key)
            t_meta_start = time.monotonic()

            for idx, a_uuid in enumerate(attachments_uuids):
                logger.debug("calling orthanc.SetAttachmentCustomData()",
                             series_id=series_id,
                             uuid=a_uuid,
                             index=idx,
                             total=len(attachments_uuids))
                orthanc.SetAttachmentCustomData(a_uuid, s3_custom_data)
                logger.debug("orthanc.SetAttachmentCustomData() returned",
                             series_id=series_id,
                             uuid=a_uuid,
                             index=idx)

            t_meta_done = time.monotonic()
            logger.info("SetAttachmentCustomData loop complete",
                        series_id=series_id,
                        attachment_count=len(attachments_uuids),
                        s3_key=s3_key,
                        metadata_update_ms=int((t_meta_done - t_meta_start) * 1000))

            # At this point, the local storage does not need to keep the files stored locally but there is no need to notify it.
            # In the best scenario, the files will still be stored locally at the time we need it.

            # Write a marker file so the LRU eviction guard knows this folder is safe to evict
            if local_series_folder:
                marker_path = os.path.join(
                    self._local_storage.get_folder_path(local_series_folder),
                    ".s3-uploaded"
                )
                try:
                    with open(marker_path, "w") as f:
                        f.write(s3_key)
                    logger.debug("wrote S3 upload marker file",
                                 series_id=series_id, marker_path=marker_path)
                except Exception as e:
                    logger.warning("failed to write S3 upload marker file",
                                   series_id=series_id, error=str(e))

        duration_ms = int((time.monotonic() - t0) * 1000)

        self._uncommitted_series_handler.on_committed_series(series_id=series_id)

        logger.info("series stored to S3",
                    series_id=series_id,
                    s3_key=s3_key,
                    bucket=self._bucket_name,
                    attachment_count=len(attachments_uuids),
                    zip_size_bytes=zip_size_bytes,
                    uncompressed_bytes=total_uncompressed_bytes,
                    zip_build_ms=int((t_zip_done - t0) * 1000),
                    upload_ms=int((t_upload_done - t_zip_done) * 1000),
                    metadata_update_ms=int((t_meta_done - t_meta_start) * 1000),
                    duration_ms=duration_ms)

    def _discard_zip_retrieval(self, series_id: str):
        with self._s3_zip_retrievals_lock:
            del self._s3_zip_retrievals[series_id]
            logger.debug("discarded ZipRetrieval", s3_zip_key=series_id)


    def get_s3_zip_stream(self, series_id: str):  # returns a stream
        logger.info("series zip stream from S3",
                    series_id=series_id)

        s3_zip_key = self._get_series_s3_key(series_id=series_id)

        response =  self._s3_client.get_object(Bucket=self._bucket_name,
                                               Key=s3_zip_key)
        return response['Body']


    def retrieve_zip_from_s3(self, s3_zip_key: str, local_series_folder: str):
        # make sure we do not retrieve the same file multiple times at the same time
        is_new_retrieval = False
        with self._s3_zip_retrievals_lock:  # global lock to safely manipulate the retrieval dict
            if s3_zip_key not in self._s3_zip_retrievals:
                self._s3_zip_retrievals[s3_zip_key] = LocalToS3ZipManager.ZipRetrieval(s3_zip_key, manager=self)
                is_new_retrieval = True
            zip_retrieval = self._s3_zip_retrievals[s3_zip_key]

        logger.debug("retrieve_zip_from_s3 entered",
                     s3_zip_key=s3_zip_key,
                     local_series_folder=local_series_folder,
                     is_new_retrieval=is_new_retrieval)

        with zip_retrieval: # the first thread to get here keeps the condition "locked" during the zip retrieval
            if not zip_retrieval.downloaded:
                logger.debug("this thread will perform the S3 download",
                             s3_zip_key=s3_zip_key)
                self._retrieve_zip_from_s3(s3_zip_key, local_series_folder)
                zip_retrieval.set_downloaded()
            else:
                logger.debug("another thread already downloaded this zip, waiting",
                             s3_zip_key=s3_zip_key)
                zip_retrieval.wait_downloaded()


    def _retrieve_zip_from_s3(self, s3_zip_key: str, local_series_folder: str):
        logger.info("series retrieval from S3 starting",
                    s3_zip_key=s3_zip_key,
                    bucket=self._bucket_name,
                    local_series_folder=local_series_folder)
        t0 = time.monotonic()

        file_count = 0
        total_bytes = 0

        with tempfile.NamedTemporaryFile(delete=True, suffix=".zip") as tmp_zip:
            logger.debug("downloading zip from S3",
                         s3_zip_key=s3_zip_key,
                         bucket=self._bucket_name,
                         tmp_path=tmp_zip.name)
            logger.debug("calling s3_client.download_file()",
                         s3_zip_key=s3_zip_key,
                         bucket=self._bucket_name,
                         tmp_path=tmp_zip.name)

            self._s3_client.download_file(self._bucket_name,
                                          s3_zip_key,
                                          tmp_zip.name)

            t_download_done = time.monotonic()
            zip_size_bytes = os.path.getsize(tmp_zip.name)
            logger.debug("s3_client.download_file() returned",
                         s3_zip_key=s3_zip_key,
                         zip_size_bytes=zip_size_bytes)
            logger.info("zip downloaded from S3",
                        s3_zip_key=s3_zip_key,
                        bucket=self._bucket_name,
                        zip_size_bytes=zip_size_bytes,
                        download_ms=int((t_download_done - t0) * 1000))

            logger.debug("extracting zip to local storage",
                         s3_zip_key=s3_zip_key,
                         local_series_folder=local_series_folder)

            with zipfile.ZipFile(tmp_zip.name, 'r') as zipf:
                for file_info in zipf.infolist():
                    with zipf.open(file_info) as f:
                        content = f.read()
                        self._local_storage.write_file(uuid=file_info.filename,
                                                       local_series_folder=local_series_folder,
                                                       content=content)
                        file_count += 1
                        total_bytes += len(content)
                        logger.debug("extracted file from zip to local storage",
                                     s3_zip_key=s3_zip_key,
                                     uuid=file_info.filename,
                                     size_bytes=len(content),
                                     index=file_count)

        duration_ms = int((time.monotonic() - t0) * 1000)

        logger.info("series retrieved from S3",
                    s3_zip_key=s3_zip_key,
                    bucket=self._bucket_name,
                    local_series_folder=local_series_folder,
                    file_count=file_count,
                    zip_size_bytes=zip_size_bytes,
                    uncompressed_bytes=total_bytes,
                    download_ms=int((t_download_done - t0) * 1000),
                    duration_ms=duration_ms)


    def _get_instances_attachments(self, series_id: str) -> List[str]:
        logger.info("querying Orthanc for series instance attachments", series_id=series_id)
        t0 = time.monotonic()

        payload = {
            "Level": "Instance",
            "Query": {},
            "ResponseContent": ["Attachments"],
            "ParentSeries": series_id
        }
        logger.debug("calling orthanc.RestApiPost(/tools/find)", series_id=series_id)
        response_raw = orthanc.RestApiPost("/tools/find", json.dumps(payload).encode('utf-8'))
        logger.debug("orthanc.RestApiPost(/tools/find) returned",
                     series_id=series_id,
                     response_bytes=len(response_raw))

        instances_info = json.loads(response_raw)
        supported_content_types = {
            1,  # ContentType.DICOM
            3,  # ContentType.DICOM_UNTIL_PIXEL_DATA
        }
        attachments_uuids = []
        for i in instances_info:
            for attachment in i["Attachments"]:
                if attachment["ContentType"] in supported_content_types:
                    attachments_uuids.append(attachment["Uuid"])

        duration_ms = int((time.monotonic() - t0) * 1000)
        logger.info("Orthanc returned instance attachments",
                    series_id=series_id,
                    instance_count=len(instances_info),
                    attachment_count=len(attachments_uuids),
                    query_ms=duration_ms)

        return attachments_uuids

    def get_series_info(self, series_id: str) -> Optional[SeriesS3Info]:
        attachments_uuids = self._get_instances_attachments(series_id=series_id)

        if len(attachments_uuids) == 0:
            return None

        status = SeriesS3Info(series_id=series_id)

        # get the custom data of a random attachment (the first one)
        cd = CustomData.from_orthanc_attachment(attachment_uuid=attachments_uuids[0])
        if cd:
            status.is_stored_in_s3 = cd.storage == CustomData.Storage.S3_ZIP
            if status.is_stored_in_s3:
                status.s3_zip_key = cd.s3_zip_key

        return status
    
