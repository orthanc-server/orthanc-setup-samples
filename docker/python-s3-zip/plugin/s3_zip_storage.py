import orthanc
import json
import os
import threading
import time
from helpers import Helpers
from typing import Optional, Tuple
from boto3 import client as S3Client
from local_storage import LocalStorage
from local_to_s3_zip_manager import (
    DEFAULT_COPY_QUEUE_LEASE_TIMEOUT_SECONDS,
    DEFAULT_S3_RETRIEVAL_MAX_ATTEMPTS,
    DEFAULT_S3_RETRIEVAL_RETRY_BASE_DELAY_SECONDS,
    DEFAULT_S3_RETRIEVAL_RETRY_MAX_DELAY_SECONDS,
    DEFAULT_HOUSEKEEPER_INTERVAL_SECONDS,
    LocalToS3ZipManager,
    SeriesS3Info,
)
from uncommitted_series_handler import UncommittedSeriesHandler, UNCOMMITTED_SERIES_KVS
from custom_data import CustomData
from s3zip_logging import get_logger

logger = get_logger(__name__)


# Grace period before the housekeeper treats an uncommitted-series KVS
# entry as "stuck". STABLE_SERIES normally fires within ~60s of the last
# instance; we leave several minutes of headroom so that a busy server
# with slow stability timers is not constantly fighting the natural
# copy path.
_UNCOMMITTED_MIN_AGE_SEC = 5 * 60
_BROKEN_STUDY_REUPLOAD_MESSAGE = (
    "Study storage metadata is broken or incomplete; delete the study from Orthanc and re-upload it."
)
_SUPPORTED_ATTACHMENT_CONTENT_TYPES = {
    1,  # ContentType.DICOM
    3,  # ContentType.DICOM_UNTIL_PIXEL_DATA
}


def _parse_uncommitted_entry_age_ms(raw_value, now_epoch_ms: int) -> int:
    """Return how old an uncommitted-series KVS entry is, in milliseconds.

    The KVS value is an epoch-millisecond timestamp recorded by
    ``UncommittedSeriesHandler.on_new_series``. Legacy entries written by
    older versions of the plugin (or any unparseable value) are treated as
    very old so the housekeeper still acts on them rather than ignoring
    them forever.
    """
    try:
        if isinstance(raw_value, (bytes, bytearray)):
            text = raw_value.decode("utf-8", errors="replace").strip()
        else:
            text = str(raw_value).strip()
        if not text or text == "0":
            return now_epoch_ms  # legacy sentinel: assume "very old"
        stored_ms = int(text)
        if stored_ms <= 0:
            return now_epoch_ms
        return max(0, now_epoch_ms - stored_ms)
    except Exception:
        return now_epoch_ms


def _custom_data_size(custom_data: bytes) -> int:
    try:
        return len(custom_data)
    except Exception:
        return -1


class S3ZipStorage:

    _local_storage: LocalStorage
    _zip_manager: LocalToS3ZipManager
    _uncommitted_series_handler: UncommittedSeriesHandler
    _housekeeper_enabled: bool = False
    _housekeeper_interval_sec: float
    _housekeeper_timer: threading.Timer | None = None

    def __init__(self,
                 temporary_folder_root: str,
                 temp_folder_max_size_mb: int,
                 s3_client: S3Client,
                 bucket_name: str,
                 enable_compression: bool,
                 key_prefix: str = "",
                 s3_retrieval_max_attempts: int = DEFAULT_S3_RETRIEVAL_MAX_ATTEMPTS,
                 s3_retrieval_retry_base_delay_sec: float = DEFAULT_S3_RETRIEVAL_RETRY_BASE_DELAY_SECONDS,
                 s3_retrieval_retry_max_delay_sec: float = DEFAULT_S3_RETRIEVAL_RETRY_MAX_DELAY_SECONDS,
                 copy_queue_lease_timeout_sec: int = DEFAULT_COPY_QUEUE_LEASE_TIMEOUT_SECONDS,
                 housekeeper_interval_sec: float = DEFAULT_HOUSEKEEPER_INTERVAL_SECONDS):
        logger.debug("initializing S3ZipStorage",
                     temp_folder=temporary_folder_root,
                     max_size_mb=temp_folder_max_size_mb,
                     bucket=bucket_name,
                     compression=enable_compression,
                     key_prefix=key_prefix or "<none>",
                     s3_retrieval_max_attempts=s3_retrieval_max_attempts,
                     s3_retrieval_retry_base_delay_sec=s3_retrieval_retry_base_delay_sec,
                     s3_retrieval_retry_max_delay_sec=s3_retrieval_retry_max_delay_sec,
                     copy_queue_lease_timeout_sec=copy_queue_lease_timeout_sec,
                     housekeeper_interval_sec=housekeeper_interval_sec)

        self._uncommitted_series_handler = UncommittedSeriesHandler()

        self._local_storage: LocalStorage = LocalStorage(root=temporary_folder_root,
                                           max_size_mb=temp_folder_max_size_mb)

        self._zip_manager = LocalToS3ZipManager(s3_client=s3_client,
                                                bucket_name=bucket_name,
                                                local_storage=self._local_storage,
                                                enable_compression=enable_compression,
                                                uncommitted_series_handler=self._uncommitted_series_handler,
                                                key_prefix=key_prefix,
                                                s3_retrieval_max_attempts=s3_retrieval_max_attempts,
                                                s3_retrieval_retry_base_delay_sec=s3_retrieval_retry_base_delay_sec,
                                                s3_retrieval_retry_max_delay_sec=s3_retrieval_retry_max_delay_sec,
                                                copy_queue_lease_timeout_sec=copy_queue_lease_timeout_sec)

        # Set up the eviction guard: a folder is safe to evict only if it has the
        # .s3-uploaded marker file written by the copy thread after a successful S3 upload.
        def _is_folder_safe_to_evict(folder_name: str) -> bool:
            marker_path = os.path.join(self._local_storage.get_folder_path(folder_name), ".s3-uploaded")
            return os.path.exists(marker_path)

        self._local_storage.set_eviction_guard(_is_folder_safe_to_evict)
        self._housekeeper_interval_sec = housekeeper_interval_sec
        self._housekeeper_enabled = housekeeper_interval_sec >= 1

        logger.debug("S3ZipStorage initialized")

    def evict_local_cache(self) -> dict[str, int]:
        """Force-evict every locally-cached series already on S3.

        Returns a JSON-friendly dict (folders evicted, bytes freed, folders
        skipped because not yet uploaded, available bytes after, max bytes).
        """
        result = self._local_storage.evict_all_safe()
        return {
            "freed_folders": result.freed_folders,
            "freed_bytes": result.freed_bytes,
            "skipped_folders": result.skipped_folders,
            "available_bytes": result.available_bytes_after,
            "max_bytes": self._local_storage._max_size,
        }

    def get_local_cache_stats(self) -> dict:
        """Return a snapshot of local-cache occupancy without triggering eviction."""
        return self._local_storage.get_cache_summary()

    def start(self):
        logger.debug("starting S3ZipStorage manager")
        self._zip_manager.start()

        if self._housekeeper_enabled:
            logger.debug(f"Scheduling housekeeper with an interval of {self._housekeeper_interval_sec} sec")
            self._schedule_housekeeping()
        else:
            logger.debug(f"NOT starting housekeeper")


    def stop(self):
        logger.debug("stopping S3ZipStorage manager")
        self._zip_manager.stop()

        if self._housekeeper_timer:
            logger.debug("stopping housekeeper")
            self._housekeeper_timer.cancel()


    def on_new_series(self, series_id: str):
        self._uncommitted_series_handler.on_new_series(series_id=series_id)

    def storage_create(self,
                       uuid: str,
                       content_type: orthanc.ContentType,
                       compression_type: orthanc.CompressionType,
                       content: bytes,
                       dicom_instance: orthanc.DicomInstance) -> tuple[orthanc.ErrorCode, bytes | None]:

        logger.debug("storage_create entered",
                     uuid=uuid,
                     content_type=str(content_type),
                     size_bytes=len(content))

        if content_type not in (orthanc.ContentType.DICOM, orthanc.ContentType.DICOM_UNTIL_PIXEL_DATA):
            logger.debug("storage_create: ignoring unsupported content type",
                         uuid=uuid,
                         content_type=str(content_type))
            return orthanc.ErrorCode.SUCCESS, None

        logger.debug("calling Helpers.get_series_hash()", uuid=uuid)
        series_hash = Helpers.get_series_hash(dicom_instance)
        logger.debug("Helpers.get_series_hash() returned", uuid=uuid, series_hash=series_hash)

        logger.debug("storage_create called",
                     uuid=uuid,
                     content_type=str(content_type),
                     compression_type=str(compression_type),
                     size_bytes=len(content),
                     series_hash=series_hash)

        # we always write only to the local storage
        logger.debug("calling local_storage.create()", uuid=uuid, series_hash=series_hash)
        error_code = self._local_storage.create(uuid=uuid,
                                                local_series_folder=series_hash,
                                                content_type=content_type,
                                                compression_type=compression_type,
                                                content=content)
        logger.debug("local_storage.create() returned", uuid=uuid, error_code=str(error_code))

        # Any new file invalidates "everything in this folder is on S3". Wipe
        # the marker so eviction cannot purge the folder before the next copy
        # captures this instance. The per-folder critical section pairs with
        # the matching one in copy_series_to_s3 around its recheck+marker
        # write: ordering between the two is now sequential, so a stale
        # marker cannot be published after this invalidate runs as a no-op.
        # Idempotent on a missing marker, so safe to call even when create()
        # failed.
        with self._local_storage.folder_marker_critical_section(series_hash):
            _ = self._zip_manager.invalidate_s3_uploaded_marker(local_series_folder=series_hash)

        custom_data = CustomData(CustomData.Storage.LOCAL,
                                 local_series_folder=series_hash,
                                 size_in_bytes=len(content))

        logger.debug("storage_create completed",
                     uuid=uuid,
                     series_hash=series_hash,
                     error_code=str(error_code),
                     storage=custom_data.storage.value)

        return error_code, custom_data.to_binary()


    def storage_read_range(self,
                           uuid: str,
                           content_type: orthanc.ContentType,
                           range_start: int,
                           size: int,
                           custom_data: bytes) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:

        logger.debug("storage_read_range entered",
                     uuid=uuid,
                     content_type=str(content_type),
                     range_start=range_start,
                     size=size)

        cd: CustomData | None = self._load_custom_data_or_log_broken(
            uuid=uuid,
            content_type=content_type,
            custom_data=custom_data,
            operation="storage_read_range",
        )
        if cd is None:
            return orthanc.ErrorCode.UNKNOWN_RESOURCE, None

        logger.debug("storage_read_range called",
                     uuid=uuid,
                     content_type=str(content_type),
                     range_start=range_start,
                     size=size,
                     storage=cd.storage.value,
                     local_series_folder=cd.local_series_folder,
                     s3_zip_key=cd.s3_zip_key or "<none>")

        # Eviction removes whole series folders. Keep the folder leased from the
        # local existence check through the final read so a safe-to-evict folder
        # cannot disappear between `has_local_file()` and `read_range()`.
        with self._local_storage.lease_folder(cd.local_series_folder):
            logger.debug("calling local_storage.has_local_file()", uuid=uuid)
            has_local = self._local_storage.has_local_file(uuid=uuid,
                                                           local_series_folder=cd.local_series_folder,
                                                           content_type=content_type)
            logger.debug("local_storage.has_local_file() returned", uuid=uuid, has_local=has_local)

            if not has_local:
                s3_zip_key = cd.s3_zip_key

                if s3_zip_key is None:
                    # Custom data can still point to local storage after a pod restart
                    # or cache eviction. A completed upload leaves a marker in the
                    # series folder so reads can recover the S3 key without querying
                    # every instance attachment again.
                    marker_path = os.path.join(
                        self._local_storage.get_folder_path(cd.local_series_folder),
                        ".s3-uploaded"
                    )
                    if os.path.exists(marker_path):
                        with open(marker_path, "r") as f:
                            s3_zip_key = f.read().strip()
                        logger.warning(
                            "instance marked as local but file is gone; recovered S3 key from marker",
                            uuid=uuid,
                            s3_zip_key=s3_zip_key,
                            local_series_folder=cd.local_series_folder)
                    else:
                        logger.error(
                            "instance marked as local but file is gone and no S3 key available. "
                            f"{_BROKEN_STUDY_REUPLOAD_MESSAGE}",
                            uuid=uuid,
                            series_id=cd.series_id or "<unknown>",
                            local_series_folder=cd.local_series_folder)
                        return orthanc.ErrorCode.UNKNOWN_RESOURCE, None

                logger.debug("instance not in local cache, retrieving series from S3",
                             uuid=uuid,
                             s3_zip_key=s3_zip_key,
                             local_series_folder=cd.local_series_folder)
                logger.debug("calling zip_manager.retrieve_zip_from_s3()", uuid=uuid, s3_zip_key=s3_zip_key)
                try:
                    self._zip_manager.retrieve_zip_from_s3(s3_zip_key=s3_zip_key,
                                                           local_series_folder=cd.local_series_folder)
                except Exception as e:
                    logger.error(
                        "failed to retrieve backing S3 zip while reading instance. "
                        f"{_BROKEN_STUDY_REUPLOAD_MESSAGE}",
                        uuid=uuid,
                        series_id=cd.series_id or "<unknown>",
                        s3_zip_key=s3_zip_key,
                        local_series_folder=cd.local_series_folder,
                        error_type=type(e).__name__,
                        error=str(e),
                    )
                    return orthanc.ErrorCode.UNKNOWN_RESOURCE, None
                logger.debug("zip_manager.retrieve_zip_from_s3() returned", uuid=uuid)
                logger.debug("series retrieved from S3 into local cache",
                             uuid=uuid,
                             s3_zip_key=s3_zip_key)
            else:
                logger.debug("instance found in local cache",
                             uuid=uuid,
                             local_series_folder=cd.local_series_folder)

            logger.debug("calling local_storage.read_range()", uuid=uuid, range_start=range_start, size=size)
            result = self._local_storage.read_range(uuid=uuid,
                                                    local_series_folder=cd.local_series_folder,
                                                    content_type=content_type,
                                                    range_start=range_start,
                                                    size=size)
            logger.debug("local_storage.read_range() returned", uuid=uuid)

        error_code, data = result
        logger.debug("storage_read_range completed",
                     uuid=uuid,
                     error_code=str(error_code),
                     bytes_read=len(data) if data else 0)

        if error_code != orthanc.ErrorCode.SUCCESS:
            logger.error(
                "storage_read_range could not read instance bytes. "
                f"{_BROKEN_STUDY_REUPLOAD_MESSAGE}",
                uuid=uuid,
                series_id=cd.series_id or "<unknown>",
                local_series_folder=cd.local_series_folder,
                s3_zip_key=cd.s3_zip_key or "<none>",
                error_code=str(error_code),
            )

        return result

    def storage_remove(self,
                       uuid: str,
                       content_type: orthanc.ContentType,
                       custom_data: bytes) -> orthanc.ErrorCode:

        logger.debug("storage_remove entered", uuid=uuid, content_type=str(content_type))

        cd = self._load_custom_data_or_log_broken(
            uuid=uuid,
            content_type=content_type,
            custom_data=custom_data,
            operation="storage_remove",
        )
        if cd is None:
            logger.error(
                "storage_remove cannot map this attachment to local/S3 backing storage; "
                "returning success so Orthanc can delete the DB resource. "
                f"{_BROKEN_STUDY_REUPLOAD_MESSAGE}",
                uuid=uuid,
                content_type=str(content_type),
                custom_data_size_bytes=_custom_data_size(custom_data),
            )
            return orthanc.ErrorCode.SUCCESS

        logger.debug("storage_remove called",
                     uuid=uuid,
                     content_type=str(content_type),
                     storage=cd.storage.value,
                     local_series_folder=cd.local_series_folder)

        # always delete from the local storage in case it has been stored there
        logger.debug("calling local_storage.remove()", uuid=uuid)
        try:
            self._local_storage.remove(uuid=uuid,
                                       local_series_folder=cd.local_series_folder,
                                       content_type=content_type,
                                       file_size=cd.size_in_bytes)
            logger.debug("local_storage.remove() returned", uuid=uuid)
        except Exception as e:
            logger.error(
                "storage_remove failed to clean local backing file; returning success so Orthanc can delete "
                "the DB resource. Any stale local file is best-effort cache garbage. "
                f"{_BROKEN_STUDY_REUPLOAD_MESSAGE}",
                uuid=uuid,
                series_id=cd.series_id or "<unknown>",
                local_series_folder=cd.local_series_folder,
                error_type=type(e).__name__,
                error=str(e),
            )

        if self._housekeeper_enabled and cd.series_id: # this only happens if the series has been uploaded into s3
            try:
                orthanc.StoreKeyValue("series-ids-to-possibly-delete-from-s3", cd.series_id, custom_data) # cd.s3_zip_key.encode('utf-8') if cd.s3_zip_key else b'')
            except Exception as e:
                logger.error(
                    "storage_remove could not schedule S3 zip cleanup; returning success so Orthanc can delete "
                    "the DB resource. A later re-upload of the same series will overwrite the S3 zip key; "
                    "otherwise this may leave an orphaned S3 object.",
                    uuid=uuid,
                    series_id=cd.series_id,
                    s3_zip_key=cd.s3_zip_key or "<none>",
                    error_type=type(e).__name__,
                    error=str(e),
                )
        elif self._housekeeper_enabled:
            logger.warning(
                "storage_remove custom data has no series id; S3 zip cleanup cannot be scheduled, "
                "but Orthanc DB deletion will continue. "
                f"{_BROKEN_STUDY_REUPLOAD_MESSAGE}",
                uuid=uuid,
                local_series_folder=cd.local_series_folder,
                s3_zip_key=cd.s3_zip_key or "<none>",
            )

        logger.debug("storage_remove completed", uuid=uuid)

        return orthanc.ErrorCode.SUCCESS

    def _load_custom_data_or_log_broken(self,
                                        uuid: str,
                                        content_type: orthanc.ContentType,
                                        custom_data: bytes,
                                        operation: str) -> Optional[CustomData]:
        try:
            return CustomData.from_binary(custom_data)
        except Exception as e:
            logger.error(
                f"{operation}: invalid S3Zip CustomData. {_BROKEN_STUDY_REUPLOAD_MESSAGE}",
                uuid=uuid,
                content_type=str(content_type),
                custom_data_size_bytes=_custom_data_size(custom_data),
                error_type=type(e).__name__,
                error=str(e),
            )
            return None


    def schedule_copy_series_to_s3(self, series_id: str):
        logger.debug("scheduling series copy to S3", series_id=series_id)
        self._zip_manager.schedule_copy_series_to_s3(series_id=series_id)


    def get_series_status(self, series_id: str) -> Optional[SeriesS3Info]:
        logger.debug("retrieving series S3 status", series_id=series_id)
        return self._zip_manager.get_series_info(series_id=series_id)


    def get_s3_zip_stream(self, series_id: str):  # returns a stream
        logger.debug("retrieving a series S3 zip stream", series_id=series_id)
        return self._zip_manager.get_s3_zip_stream(series_id=series_id)

    def perform_housekeeping(self):
        self._housekeeper_timer = None
        # The outer try/except guarantees the timer is rescheduled even on
        # unexpected failures inside _perform_housekeeping. Without this the
        # housekeeper could go silent for the life of the pod.
        try:
            self._perform_housekeeping()
        except Exception:
            # Per-pass and per-series guards swallow most errors. Anything
            # that still escapes is a real bug; log with the traceback so
            # the next run can be diagnosed instead of silently lost.
            logger.exception("Housekeeper: unexpected error during run; rescheduling anyway")
        finally:
            # reschedule
            self._schedule_housekeeping()

    def _schedule_housekeeping(self):
        self._housekeeper_timer = threading.Timer(self._housekeeper_interval_sec, self.perform_housekeeping)
        self._housekeeper_timer.start()

    def _perform_housekeeping(self):
        logger.debug("Performing housekeeping")

        # Each pass is independent: a failure in one must not prevent the
        # others from running. Pass-level guards turn unexpected failures
        # into a logged warning so the timer keeps ticking.
        try:
            self._housekeep_deleted_series()
        except Exception:
            logger.exception("Housekeeper: deleted-series pass failed")

        try:
            self._housekeep_uncommitted_series()
        except Exception:
            logger.exception("Housekeeper: uncommitted-series pass failed")

        logger.debug("Performed housekeeping")

    def _housekeep_deleted_series(self):
        """Pass 1 -- clean up S3 zips for series that have been removed from Orthanc.

        Driven by the ``series-ids-to-possibly-delete-from-s3`` KVS, which is
        populated by ``storage_remove`` for every attachment that was on S3
        when it got deleted. For each entry: if Orthanc still has the series
        (an instance has been added back), drop the KVS entry; otherwise
        delete the S3 zip and drop the entry.

        Resilience:
          - Every per-series operation is wrapped in its own try/except so a
            single corrupt entry, S3 error, or transient PostgreSQL hiccup
            cannot stop the rest of the pass.
          - KVS entries are deleted incrementally (rather than at the end of
            the loop) so a mid-pass crash does not lose progress.
          - Race protection against "series re-created between the
            existence check and the S3 delete": after a successful S3
            delete we re-query Orthanc; if the series is back with
            ``CustomData.storage == s3-zip`` pointing at the same key, we
            re-schedule a copy so the new attachment set is re-uploaded.
        """
        series_iterator = orthanc.CreateKeysValuesIterator("series-ids-to-possibly-delete-from-s3")
        while series_iterator.Next():
            try:
                series_id = series_iterator.GetKey()
            except Exception:
                logger.exception("Housekeeper: failed to read key from KVS iterator; skipping entry")
                continue

            try:
                raw_value = series_iterator.GetValue()
                cd = CustomData.from_binary(raw_value)
            except Exception:
                # A corrupt or unparseable value is not actionable. Drop it
                # rather than loop on it every run.
                logger.exception(
                    "Housekeeper: corrupt KVS value for series; dropping entry",
                    series_id=series_id,
                )
                self._safe_delete_kvs_entry("series-ids-to-possibly-delete-from-s3", series_id)
                continue

            try:
                self._housekeep_one_deleted_series(series_id=series_id, cd=cd)
            except Exception:
                # Leave the entry in the KVS so the next run can retry; the
                # operations downstream are idempotent (re-querying Orthanc,
                # re-deleting an absent S3 object, re-scheduling a copy).
                logger.exception(
                    "Housekeeper: failed to process deleted-series entry; will retry next pass",
                    series_id=series_id,
                )

    def _housekeep_one_deleted_series(self, series_id: str, cd: CustomData):
        try:
            orthanc.RestApiGet(f"/series/{series_id}/instances")
            still_in_orthanc = True
        except orthanc.OrthancException as e:
            if e.args and e.args[0] == orthanc.ErrorCode.UNKNOWN_RESOURCE:
                still_in_orthanc = False
            else:
                # Any other Orthanc error: leave entry, retry next pass.
                logger.warning(
                    "Housekeeper: unexpected Orthanc error while checking series; will retry",
                    series_id=series_id,
                    error=str(e),
                )
                return

        if still_in_orthanc:
            logger.debug(
                f"Housekeeper: the series {series_id} is STILL in Orthanc, not deleting it"
            )
            # Drop the KVS entry now. If subsequent instances of this series
            # are deleted, storage_remove will push the series back into the
            # KVS for the next pass to revisit.
            self._safe_delete_kvs_entry("series-ids-to-possibly-delete-from-s3", series_id)
            return

        if not cd.s3_zip_key:
            # Nothing to delete on S3 -- drop the KVS entry.
            self._safe_delete_kvs_entry("series-ids-to-possibly-delete-from-s3", series_id)
            return

        logger.info(
            f"Housekeeper: the series {series_id} is NOT in Orthanc, deleting its zip from S3"
        )
        self._zip_manager.delete_zip_from_s3(s3_zip_key=cd.s3_zip_key)

        # Race protection: if the series has reappeared in Orthanc during
        # our S3 delete and is already marked as ``s3-zip`` pointing at the
        # same key, we have just deleted a freshly-uploaded zip. Re-schedule
        # a copy so the next stable-series cycle re-publishes it. The
        # detection is best-effort; the next housekeeping pass will catch
        # any case we miss here.
        try:
            self._reupload_if_reappeared_during_delete(series_id=series_id, deleted_s3_key=cd.s3_zip_key)
        except Exception:
            logger.exception(
                "Housekeeper: post-delete reappearance check failed; relying on next pass",
                series_id=series_id,
            )

        self._safe_delete_kvs_entry("series-ids-to-possibly-delete-from-s3", series_id)

    def _reupload_if_reappeared_during_delete(self, series_id: str, deleted_s3_key: str) -> None:
        status = self._zip_manager.get_series_info(series_id=series_id)
        if status is None:
            return  # really gone
        if status.is_stored_in_s3 and status.s3_zip_key == deleted_s3_key:
            logger.warning(
                "Housekeeper: series re-created and uploaded during S3 delete; "
                "rescheduling copy to replace the deleted zip",
                series_id=series_id,
                s3_zip_key=deleted_s3_key,
            )
            self._zip_manager.schedule_copy_series_to_s3(series_id=series_id)

    def _housekeep_uncommitted_series(self):
        """Pass 2 -- rescue or quarantine series whose copy to S3 never completed.

        The ``uncommitted-series`` KVS is populated by ``on_new_series`` (each
        time Orthanc emits ``NEW_SERIES``) and cleared by ``on_committed_series``
        when ``copy_series_to_s3`` succeeds. An entry that lingers past the
        configured grace period (``_UNCOMMITTED_MIN_AGE_SEC`` below) is a
        series whose copy was missed -- the most common causes are:

          * ``STABLE_SERIES`` was never delivered to the s3zip on-change
            handler (e.g. earlier on-change handler in the dispatcher
            raised, pod was SIGTERM'd before the stability timer fired).
          * The copy-thread enqueue or the worker itself crashed.
          * The reservation was released but the worker is now hitting a
            persistent failure (e.g. local files wiped after a restart).

        Action:
          * If at least one instance is still readable from local disk,
            re-schedule a copy. The copy thread is idempotent (same s3 key,
            overwrites), and its own recheck-then-marker logic handles a
            concurrent stable-series-driven copy gracefully.
          * If no local data is reachable AND the series has no S3 zip
            either, log a warning at WARNING level and quarantine the
            series_id in a separate KVS for operator visibility. We do NOT
            auto-delete -- the index record may be the only evidence the
            series existed.

        Resilience: each per-series action is wrapped in its own try/except;
        the iterator itself is also guarded. The KVS entry is left in place
        when we trigger a copy -- ``on_committed_series`` is the only path
        that removes it. For lost series, the entry is moved into the
        quarantine KVS so the next pass does not keep retrying.
        """
        try:
            series_iterator = orthanc.CreateKeysValuesIterator(UNCOMMITTED_SERIES_KVS)
        except Exception:
            logger.exception("Housekeeper: failed to open uncommitted-series KVS iterator")
            return

        now_epoch_ms = int(time.time() * 1000)

        while series_iterator.Next():
            try:
                series_id = series_iterator.GetKey()
                raw_value = series_iterator.GetValue()
            except Exception:
                logger.exception("Housekeeper: failed to read uncommitted-series KVS entry; skipping")
                continue

            try:
                self._housekeep_one_uncommitted_series(
                    series_id=series_id,
                    raw_value=raw_value,
                    now_epoch_ms=now_epoch_ms,
                )
            except Exception:
                logger.exception(
                    "Housekeeper: failed to process uncommitted-series entry; will retry next pass",
                    series_id=series_id,
                )

    def _housekeep_one_uncommitted_series(self, series_id: str, raw_value, now_epoch_ms: int) -> None:
        age_ms = _parse_uncommitted_entry_age_ms(raw_value=raw_value, now_epoch_ms=now_epoch_ms)
        if age_ms < _UNCOMMITTED_MIN_AGE_SEC * 1000:
            # Too young: STABLE_SERIES probably has not fired yet. Leave it
            # for a future pass.
            return

        # Does the series still exist in Orthanc? If not, the entry is
        # stale (the series was deleted before being committed, or a
        # previous startup cleanup removed it). Drop the KVS entry.
        try:
            instances_raw = orthanc.RestApiGet(f"/series/{series_id}/instances")
        except orthanc.OrthancException as e:
            if e.args and e.args[0] == orthanc.ErrorCode.UNKNOWN_RESOURCE:
                logger.info(
                    "Housekeeper: uncommitted series no longer in Orthanc; dropping KVS entry",
                    series_id=series_id,
                )
                self._safe_delete_kvs_entry(UNCOMMITTED_SERIES_KVS, series_id)
                return
            logger.warning(
                "Housekeeper: unexpected Orthanc error while inspecting uncommitted series; will retry",
                series_id=series_id,
                error=str(e),
            )
            return

        try:
            instances = json.loads(instances_raw)
        except Exception:
            logger.exception(
                "Housekeeper: could not parse /series/<id>/instances response",
                series_id=series_id,
            )
            return

        if not instances:
            # Series exists but has zero instances. Nothing to upload, the
            # entry is stale.
            logger.info(
                "Housekeeper: uncommitted series has no instances; dropping KVS entry",
                series_id=series_id,
            )
            self._safe_delete_kvs_entry(UNCOMMITTED_SERIES_KVS, series_id)
            return

        # Decide rescuable vs lost. If get_series_info reports that the
        # series is ALREADY on S3 then the on_committed_series callback was
        # missed -- treat as rescuable (calling on_committed_series here is
        # safe and idempotent on the KVS).
        try:
            status = self._zip_manager.get_series_info(series_id=series_id)
        except Exception:
            logger.exception(
                "Housekeeper: get_series_info failed; will retry next pass",
                series_id=series_id,
            )
            return

        if status is not None and status.is_stored_in_s3:
            logger.warning(
                "Housekeeper: series is on S3 but KVS still marks it as uncommitted; "
                "clearing stale entry",
                series_id=series_id,
                s3_zip_key=status.s3_zip_key,
            )
            self._uncommitted_series_handler.on_committed_series(series_id=series_id)
            return

        # Count how many instances still have at least one attachment file
        # on local disk. ``has_local_file`` is cheap (an os.path.exists)
        # so it is safe to call for every instance.
        instances_with_local_file, total_probed, first_local_folder, probe_failed = self._probe_instance_local_files(
            series_id=series_id,
        )
        if probe_failed:
            return

        # Three branches, all of which schedule a copy. The copy thread
        # has its own fast-path guard that ack's without re-enqueueing
        # when local data is missing -- so we won't spin the queue.
        #
        # NOTE on observability: today the "tainted" / "lost" branches
        # only emit an ERROR log. Future work: tag the Orthanc series
        # with a metadata key (e.g. ``S3ZipDataLost`` /
        # ``S3ZipDataTainted`` plus a timestamp + reason) so the
        # housekeeper can enumerate non-rescuable series via a single
        # /tools/find rather than scraping log files (so that we can
        # report on them ata hgigher level). The current quarantine
        # KVS is a placeholder until we add metadata support.
        if total_probed > 0 and instances_with_local_file == total_probed:
            logger.warning(
                "Housekeeper: uncommitted series still has local data for ALL probed instances, "
                "scheduling copy to S3",
                series_id=series_id,
                age_sec=int(age_ms / 1000),
                instances_with_local_file=instances_with_local_file,
                total_probed=total_probed,
                local_series_folder=first_local_folder,
            )
        elif instances_with_local_file > 0:
            logger.error(
                "Housekeeper: uncommitted series is TAINTED (only some instances have local data); "
                "triggering copy so the failure is visible",
                series_id=series_id,
                age_sec=int(age_ms / 1000),
                instances_with_local_file=instances_with_local_file,
                total_probed=total_probed,
                local_series_folder=first_local_folder,
            )
            # TODO: tag the series with an Orthanc metadata key
            # (e.g. ``S3ZipDataTainted=<epoch_ms>:<count_present>/<count_total>``)
            # so the housekeeper can enumerate tainted series without
            # scraping logs. Same goes for the "lost" branch below.
        else:
            logger.error(
                "Housekeeper: uncommitted series has NO recoverable local data; "
                "triggering copy so the failure surfaces in the copy thread's guard",
                series_id=series_id,
                age_sec=int(age_ms / 1000),
                instances_with_local_file=instances_with_local_file,
                total_probed=total_probed,
            )
            # TODO: tag the series with ``S3ZipDataLost=<epoch_ms>`` (see
            # note above). For now the copy thread will log a matching
            # ERROR and acknowledge without re-enqueueing, after which
            # the on_committed_series callback clears the KVS entry.

        # In all three branches: schedule the copy. The copy thread's
        # guard handles the rest -- a clean upload if data is complete,
        # an acknowledged-without-retry abandon if it is not.
        try:
            self._zip_manager.schedule_copy_series_to_s3(series_id=series_id)
        except Exception:
            logger.exception(
                "Housekeeper: schedule_copy_series_to_s3 failed; will retry next pass",
                series_id=series_id,
            )

    def _probe_instance_local_files(self, series_id: str):
        """Return local-file probe counts plus whether the probe was incomplete.

        ``total_probed`` counts only the instances we could actually
        inspect. If any probe error occurs, this emits one summary log line
        for the series and returns ``probe_failed=True`` so the caller can
        leave the KVS entry untouched for a later pass.
        """
        try:
            instances_info = self._get_series_attachments_for_probe(series_id=series_id)
        except Exception as e:
            logger.warning(
                "Housekeeper: attachment probe failed for series; pausing retries",
                series_id=series_id,
                instances_seen=0,
                probe_failures=1,
                first_failed_instance_id="<bulk-query>",
                sample_error=f"{type(e).__name__}: {e}",
            )
            return 0, 0, None, True

        instances_with_local_file = 0
        total_probed = 0
        first_local_folder = None
        instances_seen = 0
        probe_errors: list[tuple[str, str]] = []

        for instance in instances_info:
            instances_seen += 1
            instance_id = instance.get("ID") if isinstance(instance, dict) else None
            attachments = instance.get("Attachments") if isinstance(instance, dict) else None
            if not instance_id or not isinstance(attachments, list):
                probe_errors.append((
                    instance_id or "<unknown>",
                    "ValueError: malformed /tools/find instance attachment response",
                ))
                continue

            attachment_uuids = []
            for attachment in attachments:
                if not isinstance(attachment, dict):
                    probe_errors.append((
                        instance_id,
                        "ValueError: malformed attachment entry",
                    ))
                    continue
                if attachment.get("ContentType") not in _SUPPORTED_ATTACHMENT_CONTENT_TYPES:
                    continue
                a_uuid = attachment.get("Uuid")
                if a_uuid:
                    attachment_uuids.append(a_uuid)
                else:
                    probe_errors.append((
                        instance_id,
                        "ValueError: supported attachment is missing Uuid",
                    ))

            if not attachment_uuids:
                # An instance with no attachments doesn't participate in
                # the local-file count -- nothing to upload anyway.
                continue
            total_probed += 1

            for a_uuid in attachment_uuids:
                try:
                    cd = CustomData.from_orthanc_attachment(attachment_uuid=a_uuid)
                except Exception as e:
                    probe_errors.append((
                        instance_id,
                        f"{type(e).__name__}: {e}",
                    ))
                    cd = None
                if cd is None:
                    continue
                if first_local_folder is None:
                    first_local_folder = cd.local_series_folder
                try:
                    if self._local_storage.has_local_file(
                        uuid=a_uuid,
                        local_series_folder=cd.local_series_folder,
                        content_type=orthanc.ContentType.DICOM,
                    ):
                        instances_with_local_file += 1
                        break
                except Exception as e:
                    probe_errors.append((
                        instance_id,
                        f"{type(e).__name__}: {e}",
                    ))

        if probe_errors:
            first_failed_instance_id, sample_error = probe_errors[0]
            logger.warning(
                "Housekeeper: attachment probe failed for series; pausing retries",
                series_id=series_id,
                instances_seen=instances_seen,
                probe_failures=len(probe_errors),
                first_failed_instance_id=first_failed_instance_id,
                sample_error=sample_error,
            )
            return instances_with_local_file, total_probed, first_local_folder, True

        return instances_with_local_file, total_probed, first_local_folder, False

    def _get_series_attachments_for_probe(self, series_id: str):
        payload = {
            "Level": "Instance",
            "Query": {},
            "ResponseContent": ["Attachments"],
            "ParentSeries": series_id,
        }
        raw = orthanc.RestApiPost("/tools/find", json.dumps(payload).encode("utf-8"))
        instances_info = json.loads(raw) if raw else []
        if not isinstance(instances_info, list):
            raise ValueError("/tools/find did not return a list")
        return instances_info

    def _safe_delete_kvs_entry(self, kvs_name: str, key: str) -> None:
        try:
            orthanc.DeleteKeyValue(kvs_name, key)
        except Exception:
            # Loss is tolerable: the next pass will re-process the entry,
            # and the downstream actions are idempotent.
            logger.exception(
                "Housekeeper: failed to delete KVS entry; will be retried",
                kvs_name=kvs_name,
                key=key,
            )
