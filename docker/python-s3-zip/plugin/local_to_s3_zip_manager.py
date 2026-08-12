import orthanc
import json
import zipfile
import os
import random
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from typing import List, Dict, Optional, Tuple

from boto3 import client as S3Client

from local_storage_interface import (
    LocalStorageInterface,
    S3_UPLOADED_MARKER_NAME,
    S3_UPLOADED_MARKER_TMP_PREFIX,
)
from uncommitted_series_handler import UncommittedSeriesHandler
from custom_data import CustomData

from s3zip_logging import get_logger
from concurrent.futures import ThreadPoolExecutor

try:
    from botocore import exceptions as botocore_exceptions
except ImportError:
    botocore_exceptions = None

logger = get_logger(__name__)

DEFAULT_S3_RETRIEVAL_MAX_ATTEMPTS = 3
DEFAULT_S3_RETRIEVAL_RETRY_BASE_DELAY_SECONDS = 0.5
DEFAULT_S3_RETRIEVAL_RETRY_MAX_DELAY_SECONDS = 5.0
DEFAULT_HOUSEKEEPER_INTERVAL_SECONDS = 300.0
DEFAULT_COPY_QUEUE_LEASE_TIMEOUT_SECONDS = 1800

CUSTOM_DATA_CREATION_NUM_THREADS = 12

_COPY_QUEUE_NAME = "series-to-copy"
_COPY_QUEUE_IDLE_SLEEP_SECONDS = 1

# How many series in a row may be found still in retry-backoff before the copy
# thread sleeps for one idle period. Without a bound, a queue holding only
# backing-off series would be dequeued/re-enqueued in a hot loop; with it, the
# thread still checks every entry promptly but cannot spin.
_COPY_QUEUE_MAX_DEFERRALS_BEFORE_IDLE = 5


_TRANSIENT_CLIENT_ERROR_CODES = {
    "InternalError",
    "InternalFailure",
    "RequestTimeout",
    "RequestTimeoutException",
    "ServiceUnavailable",
    "SlowDown",
    "ThrottledException",
    "Throttling",
    "ThrottlingException",
    "TooManyRequestsException",
}

_PERMANENT_CLIENT_ERROR_CODES = {
    "AccessDenied",
    "InvalidAccessKeyId",
    "InvalidObjectState",
    "NoSuchBucket",
    "NoSuchKey",
    "SignatureDoesNotMatch",
}

_TRANSIENT_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}

if botocore_exceptions is not None:
    ClientError = getattr(botocore_exceptions, "ClientError", None)
    _TRANSIENT_BOTOCORE_EXCEPTIONS = tuple(
        getattr(botocore_exceptions, name)
        for name in (
            "ConnectionClosedError",
            "ConnectTimeoutError",
            "EndpointConnectionError",
            "ProxyConnectionError",
            "ReadTimeoutError",
        )
        if hasattr(botocore_exceptions, name)
    )
else:
    ClientError = None
    _TRANSIENT_BOTOCORE_EXCEPTIONS = ()


# Series that lost at least one attachment: bytes Orthanc still lists but that
# exist neither on local disk nor in any S3 zip. Written by copy_series_to_s3,
# read by the per-series status endpoint, dropped by the housekeeper when the
# series leaves Orthanc.
#
# The point is enumerability. Until now the only trace of destroyed data was an
# ERROR line in a container log -- which in the CI run that motivated this was
# rotated away before anyone looked. A KVS entry survives, can be listed, and
# gives the Gap Server a truthful answer to "is this study whole?".
LOST_DATA_KVS = "s3zip-series-with-lost-data"


class SeriesS3Info:

    series_id: str
    is_stored_in_s3: bool = False
    s3_zip_key: str = None
    lost_attachment_count: int = 0

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
        _downloaded: bool
        _failed_exception: Optional[BaseException]

        def __init__(self, series_id: str):
            self.series_id = series_id
            self._condition = threading.Condition()
            self._ref_count = 0
            self._downloaded = False
            self._failed_exception = None
            logger.debug("ZipRetrieval created", series_id=series_id)

        def __enter__(self):
            logger.debug("ZipRetrieval entering (acquiring condition)",
                         series_id=self.series_id,
                         ref_count=self._ref_count)
            self._condition.__enter__()
            logger.debug("ZipRetrieval entered (condition acquired)",
                         series_id=self.series_id,
                         ref_count=self._ref_count)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            logger.debug("ZipRetrieval exiting",
                         series_id=self.series_id,
                         ref_count=self._ref_count)
            self._condition.__exit__(exc_type, exc_val, exc_tb)
            logger.debug("ZipRetrieval exited",
                         series_id=self.series_id,
                         ref_count=self._ref_count)

        @property
        def downloaded(self):
            return self._downloaded

        @property
        def failed_exception(self):
            return self._failed_exception

        def set_downloaded(self):
            logger.debug("ZipRetrieval set_downloaded, notifying waiters",
                         series_id=self.series_id)
            self._downloaded = True
            self._condition.notify_all()

        def set_failed(self, exc: BaseException):
            logger.debug("ZipRetrieval set_failed, notifying waiters",
                         series_id=self.series_id,
                         error_type=type(exc).__name__,
                         error=str(exc))
            self._failed_exception = exc
            self._condition.notify_all()

        def raise_if_failed(self):
            if self._failed_exception is not None:
                raise self._failed_exception

        def wait_downloaded(self):
            logger.debug("ZipRetrieval waiting for download to complete",
                         series_id=self.series_id)
            while not self._downloaded and self._failed_exception is None:
                self._condition.wait()
            self.raise_if_failed()
            logger.debug("ZipRetrieval download wait completed",
                         series_id=self.series_id)

    _s3_client: S3Client
    _local_storage: LocalStorageInterface
    _uncommitted_series_handler: UncommittedSeriesHandler
    _bucket_name: str
    _s3_zip_retrievals: Dict[str, ZipRetrieval]
    _s3_zip_retrievals_lock: threading.Lock
    _copy_thread: threading.Thread
    _threads_should_stop: bool
    _zip_compression: int
    _s3_retrieval_max_attempts: int
    _s3_retrieval_retry_base_delay_sec: float
    _s3_retrieval_retry_max_delay_sec: float
    _copy_queue_lease_timeout_sec: int

    def __init__(self,
                 s3_client: S3Client,
                 bucket_name: str,
                 local_storage: LocalStorageInterface,
                 enable_compression: bool,
                 uncommitted_series_handler: UncommittedSeriesHandler,
                 key_prefix: str = "",
                 s3_retrieval_max_attempts: int = DEFAULT_S3_RETRIEVAL_MAX_ATTEMPTS,
                 s3_retrieval_retry_base_delay_sec: float = DEFAULT_S3_RETRIEVAL_RETRY_BASE_DELAY_SECONDS,
                 s3_retrieval_retry_max_delay_sec: float = DEFAULT_S3_RETRIEVAL_RETRY_MAX_DELAY_SECONDS,
                 copy_queue_lease_timeout_sec: int = DEFAULT_COPY_QUEUE_LEASE_TIMEOUT_SECONDS):
        self._s3_client = s3_client
        self._bucket_name = bucket_name
        self._local_storage = local_storage
        self._uncommitted_series_handler = uncommitted_series_handler
        self._key_prefix = key_prefix.strip('/')
        self._s3_retrieval_max_attempts = max(1, int(s3_retrieval_max_attempts))
        self._s3_retrieval_retry_base_delay_sec = max(0.0, float(s3_retrieval_retry_base_delay_sec))
        self._s3_retrieval_retry_max_delay_sec = max(0.0, float(s3_retrieval_retry_max_delay_sec))
        self._copy_queue_lease_timeout_sec = max(1, int(copy_queue_lease_timeout_sec))
        if enable_compression:
            self._zip_compression = zipfile.ZIP_DEFLATED
        else:
            self._zip_compression = zipfile.ZIP_STORED
        self._s3_zip_retrievals = {}
        self._s3_zip_retrievals_lock = threading.Lock()
        self._threads_should_stop = False
        # series_id -> consecutive copy failures, for retry backoff (copy thread only)
        self._copy_failure_counts: Dict[str, int] = {}
        # series_id -> monotonic deadline before which the next attempt is
        # pointless. Held per series rather than as a sleep on the worker so
        # one failing series cannot stall the copies of every other series.
        self._copy_retry_not_before: Dict[str, float] = {}
        self._consecutive_deferrals: int = 0
        self._copy_thread = threading.Thread(target=self._copy_thread_worker)

        compression_name = "ZIP_DEFLATED" if enable_compression else "ZIP_STORED"
        logger.debug("LocalToS3ZipManager initialized",
                     bucket=bucket_name,
                     compression=compression_name,
                     key_prefix=self._key_prefix or "<none>",
                     s3_retrieval_max_attempts=self._s3_retrieval_max_attempts,
                     s3_retrieval_retry_base_delay_sec=self._s3_retrieval_retry_base_delay_sec,
                     s3_retrieval_retry_max_delay_sec=self._s3_retrieval_retry_max_delay_sec,
                     copy_queue_lease_timeout_sec=self._copy_queue_lease_timeout_sec)


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

    def _any_attachment_has_local_file(self, attachments_uuids: List[str]) -> bool:
        """Does this series still have anything on local disk?

        Deliberately cheap: it stops at the first attachment that has a file,
        which for a healthy series is the first one it looks at. It runs on
        every copy, and each attachment costs a CustomData lookup (a database
        round trip), so walking a 2000-instance series here would be a real
        tax on the hot path.

        A "no" is not a verdict. It is the normal, healthy end state of a
        series -- uploaded to S3, marker written, folder evicted -- and it is
        also what a genuine loss looks like. The caller tells them apart; see
        _collect_unrecoverable_attachments.
        """
        for a_uuid in attachments_uuids:
            try:
                cd = CustomData.from_orthanc_attachment(attachment_uuid=a_uuid)
            except Exception:
                continue
            if cd is None:
                continue
            try:
                if self._local_storage.has_local_file(
                    uuid=a_uuid,
                    local_series_folder=cd.local_series_folder,
                    content_type=orthanc.ContentType.DICOM,
                ):
                    return True
            except Exception:
                # Treat a probe error as "not present": the zip loop below
                # would surface a precise failure mode anyway.
                continue
        return False

    def _collect_unrecoverable_attachments(self, attachments_uuids: List[str]) -> List[str]:
        """Return every attachment whose bytes exist neither locally nor in a zip.

        Only ever called once a series is already known to be damaged, so the
        per-attachment CustomData round-trip it costs is paid on the failure
        path, not on every copy. The point is to report "3 instances lost", not
        "at least one".

        An attachment whose CustomData cannot be read is NOT counted as lost:
        we cannot prove anything about it, and over-reporting destroyed data is
        its own kind of harm.
        """
        unrecoverable: List[str] = []

        for a_uuid in attachments_uuids:
            try:
                cd = CustomData.from_orthanc_attachment(attachment_uuid=a_uuid)
            except Exception:
                continue
            if cd is None or cd.s3_zip_key:
                continue
            try:
                if not self._local_storage.has_local_file(
                    uuid=a_uuid,
                    local_series_folder=cd.local_series_folder,
                    content_type=orthanc.ContentType.DICOM,
                ):
                    unrecoverable.append(a_uuid)
            except Exception:
                continue

        return unrecoverable

    def _quarantine_damaged_series(self,
                                   series_id: str,
                                   attachments_uuids: List[str],
                                   unrecoverable_uuids: List[str],
                                   local_series_folder: Optional[str]) -> None:
        """Stop everything for a series that has lost instances, loudly.

        Deliberately NOT "upload what we can and carry on". This is
        neurosurgical imaging: a study that is missing an instance must never
        be quietly completed. A zip that covers 78 of 79 instances is worse
        than no zip at all, because everything downstream -- the archive
        endpoint, a later rehydration, an operator eyeballing the bucket --
        would treat it as the series. Waiting for the study to be re-sent
        costs minutes; processing incomplete anatomy costs more than that.

        So: no upload, no marker. The folder keeps its remaining instances
        (they are the only copy left of them) and stays ineligible for
        eviction, which is the correct trade -- cache space for data.

        The copy-queue entry is acknowledged WITHOUT re-enqueueing. Retrying
        cannot conjure back bytes that exist nowhere, and a series that
        re-enters the queue forever starves every other series of the single
        copy worker. The damage is instead recorded where it can be found:

          * an ERROR log line,
          * a durable entry in the lost-data KVS, which
          * the per-series status endpoint reports, which
          * the Gap Server turns into a hard, non-retriable refusal to process
            the study.

        Recovery is a re-send: with Orthanc's OverwriteInstances enabled the
        missing instance is written again, the next stable-series copy finds
        the series whole, and the damaged flag is cleared.
        """
        logger.error(
            "DATA LOSS: series has instances whose bytes exist NOWHERE -- not on local disk, "
            "not in any S3 zip. Refusing to upload a partial archive for it, and refusing to "
            "mark it as stored. This study is INCOMPLETE and must be re-sent from the "
            "modality/PACS; it will not be processed until it is.",
            series_id=series_id,
            local_series_folder=local_series_folder or "<unknown>",
            lost_attachment_count=len(unrecoverable_uuids),
            attachment_count=len(attachments_uuids),
            lost_uuids=unrecoverable_uuids[:20],
        )

        recorded = self._record_lost_attachments(series_id=series_id,
                                                 lost_uuids=unrecoverable_uuids)

        if not recorded:
            # The record is the alarm: without it the status endpoint cannot
            # report the damage and the Gap Server cannot refuse the study.
            # Keep the uncommitted-series entry so the housekeeper brings this
            # series back in a few minutes and the write is retried, rather
            # than losing the only durable trace of a destroyed instance.
            logger.error(
                "the lost-data record could not be written; leaving this series on the "
                "housekeeper's list so the alarm is raised on a later pass",
                series_id=series_id,
            )
            return

        # Clear the uncommitted-series bookkeeping so the housekeeper stops
        # rescheduling a copy that can only fail the same way. The lost-data
        # KVS is the durable record from here on, and a re-send fires
        # STABLE_SERIES on its own.
        try:
            self._uncommitted_series_handler.on_committed_series(series_id=series_id)
        except Exception:
            logger.exception(
                "could not clear the uncommitted-series KVS entry for a damaged series; "
                "the housekeeper will retry the cleanup",
                series_id=series_id,
            )

    def _files_on_disk_not_in_zip(self, local_series_folder: str, zipped_uuids: set) -> List[str]:
        """Return the folder's files that the zip we just uploaded does NOT contain.

        This is the precondition for publishing the ``.s3-uploaded`` marker,
        and it is deliberately answered from the DISK rather than from
        Orthanc's index.

        Orthanc calls the storage area's ``Create`` BEFORE it records the
        attachment in its database, so a brand-new instance can be sitting in
        this folder while ``/tools/find`` still reports the previous
        attachment set. An index-based recheck therefore sees "nothing
        changed", publishes the marker, and hands eviction permission to
        delete a file that exists in no zip anywhere. That is a permanent loss
        of a DICOM instance, and it is exactly what happened in QM-9901's
        e2e run: the copy at 08:06:27 rechecked 32 == 32 attachments and
        published the marker while instance 33 was already on disk;
        the next eviction pass took the folder, and the copy 60s later found
        an attachment with no local file and no S3 zip.

        The disk is the only party that knows the truth here, and it is
        race-free in combination with ``storage_create``'s ordering (write the
        file, THEN invalidate the marker, both under the per-folder marker
        critical section):

          * the file lands before we listdir -> we see it and withhold the marker;
          * the file lands after we listdir -> its invalidate is serialised
            behind our critical section and wipes the marker we just wrote.

        Marker files (and their tmp- partials) are excluded: they are not
        instance data. A missing folder yields an empty list -- there is
        nothing on disk that the zip fails to cover.
        """
        folder_path = self._local_storage.get_folder_path(local_series_folder)
        try:
            names = os.listdir(folder_path)
        except FileNotFoundError:
            return []
        except OSError as e:
            # Unreadable folder: we cannot prove the zip covers it, so behave
            # as if it did not. Withholding the marker is always the safe
            # direction -- it costs cache space, never data.
            logger.warning("could not list series folder before publishing the S3 marker",
                           local_series_folder=local_series_folder,
                           error=str(e))
            return ["<unreadable-folder>"]

        return sorted(
            name for name in names
            if name != S3_UPLOADED_MARKER_NAME
            and not name.startswith(S3_UPLOADED_MARKER_TMP_PREFIX)
            and name not in zipped_uuids
        )


    def _resolve_local_series_folder(self, attachments_uuids: list[str]) -> str | None:
        """Return the first readable ``local_series_folder`` across attachments.

        All instances of a series share the same folder (see the existing
        zip-build loop), so the first non-empty value is authoritative.
        Per-attachment errors are swallowed so a flaky CustomData lookup
        does not prevent resolution when other attachments still carry it.
        """
        for a_uuid in attachments_uuids:
            try:
                cd: CustomData | None = CustomData.from_orthanc_attachment(attachment_uuid=a_uuid)
            except Exception:
                continue
            if cd is None:
                continue
            if cd.local_series_folder:
                return cd.local_series_folder
        return None


    def schedule_copy_series_to_s3(self, series_id: str):
        logger.debug("enqueuing series for S3 copy", series_id=series_id)
        logger.debug("calling orthanc.EnqueueValue()", series_id=series_id)
        orthanc.EnqueueValue(_COPY_QUEUE_NAME, series_id.encode('utf-8'))
        logger.debug("orthanc.EnqueueValue() returned", series_id=series_id)
        logger.debug("series enqueued for S3 copy", series_id=series_id)


    def _copy_thread_worker(self):
        try:
            orthanc.SetCurrentThreadName("S3-COPY-THREAD")
        except BaseException as e:
            self._log_copy_thread_exception("failed to set S3 copy thread name; continuing", e)
        try:
            logger.info("S3 copy thread started",
                        copy_queue_lease_timeout_sec=self._copy_queue_lease_timeout_sec)
        except BaseException:
            pass

        while not self._threads_should_stop:
            try:
                self._copy_thread_worker_once()
            except BaseException as e:
                self._log_copy_thread_exception("unhandled failure in S3 copy thread loop; continuing", e)
                try:
                    time.sleep(_COPY_QUEUE_IDLE_SLEEP_SECONDS)
                except BaseException:
                    pass

        logger.info("S3 copy thread exiting")


    def _log_copy_thread_exception(self, message: str, exc: BaseException, **kwargs):
        try:
            logger.exception(message,
                             error_type=type(exc).__name__,
                             error=str(exc),
                             **kwargs)
        except BaseException:
            try:
                print(f"[s3zip] {message}: {type(exc).__name__}: {exc}", file=sys.stderr)
            except BaseException:
                pass


    def _copy_thread_worker_once(self):
        logger.debug("calling orthanc.ReserveQueueValue(series-to-copy)",
                     lease_timeout_sec=self._copy_queue_lease_timeout_sec)
        bseries_id, value_id = orthanc.ReserveQueueValue(
            _COPY_QUEUE_NAME,
            orthanc.QueueOrigin.FRONT,
            self._copy_queue_lease_timeout_sec,
        )
        logger.debug("orthanc.ReserveQueueValue() returned",
                     got_item=bseries_id is not None,
                     value_id=str(value_id) if value_id is not None else "<none>")

        if bseries_id is None:
            logger.debug("no series in copy queue, sleeping")
            time.sleep(_COPY_QUEUE_IDLE_SLEEP_SECONDS)
            return

        if isinstance(bseries_id, str):
            series_id = bseries_id
        else:
            try:
                series_id = bseries_id.decode('utf-8')
            except BaseException as e:
                self._log_copy_thread_exception(
                    "failed to decode series-to-copy queue value; acknowledging and continuing",
                    e,
                    value_id=str(value_id))
                self._acknowledge_copy_queue_value(value_id=value_id, series_id="<decode failed>")
                return

        if not series_id:
            self._log_copy_thread_exception(
                "empty series id in series-to-copy queue value; acknowledging and continuing",
                ValueError("empty series id"),
                value_id=str(value_id))
            self._acknowledge_copy_queue_value(value_id=value_id, series_id="<decode failed>")
            return

        logger.debug("dequeued series for S3 copy",
                     series_id=series_id,
                     value_id=str(value_id))

        if self._defer_series_still_in_backoff(series_id=series_id,
                                               bseries_id=bseries_id,
                                               value_id=value_id):
            return

        self._consecutive_deferrals = 0
        logger.info("starting copy_series_to_s3", series_id=series_id)

        copy_succeeded = False
        should_ack = True
        try:
            self.copy_series_to_s3(series_id=series_id)
            copy_succeeded = True
            self._copy_failure_counts.pop(series_id, None)
            self._copy_retry_not_before.pop(series_id, None)
        except BaseException as e:
            self._log_copy_thread_exception("failed to copy series to S3, re-enqueuing",
                                            e,
                                            series_id=series_id)
            # TODO: identify if this is a "permanent failure".  In this case, no need to repost the message + handle max retries
            try:
                logger.debug("re-enqueuing failed series via orthanc.EnqueueValue()", series_id=series_id)
                orthanc.EnqueueValue(_COPY_QUEUE_NAME, bseries_id)
                logger.debug("orthanc.EnqueueValue() returned after re-enqueue", series_id=series_id)
            except BaseException as requeue_error:
                should_ack = False
                self._log_copy_thread_exception(
                    "failed to re-enqueue failed series; leaving reserved queue value unacknowledged for lease release",
                    requeue_error,
                    series_id=series_id,
                    value_id=str(value_id))

        if should_ack:
            acknowledged = self._acknowledge_copy_queue_value(value_id=value_id, series_id=series_id)
            if acknowledged and copy_succeeded:
                logger.info("copy_series_to_s3 cycle complete", series_id=series_id)
            elif acknowledged:
                logger.info("failed copy re-enqueued and original queue value acknowledged", series_id=series_id)

        if not copy_succeeded:
            # Exponential backoff between retries of a failing copy. Without
            # it the dequeue/fail/re-enqueue cycle spins every ~20 ms, floods
            # the log and starves everything else on this thread.
            #
            # The backoff is recorded PER SERIES and enforced at dequeue time
            # (see _defer_series_still_in_backoff) rather than slept off here.
            # Sleeping on this thread would put the whole copy pipeline on
            # hold for one sick series: with a 30 s cap and a series that
            # cannot be fixed by retrying, every other series' upload -- and
            # therefore the local cache's ability to drain at all -- runs at
            # one copy per 30 s. That is how a single broken series turns
            # into a server-wide slowdown.
            failures = self._copy_failure_counts.get(series_id, 0) + 1
            self._copy_failure_counts[series_id] = failures
            backoff_sec = min(2 ** min(failures, 5), 30)
            self._copy_retry_not_before[series_id] = time.monotonic() + backoff_sec
            logger.info("backing off before next copy attempt",
                        series_id=series_id,
                        consecutive_failures=failures,
                        backoff_sec=backoff_sec)


    def _defer_series_still_in_backoff(self, series_id: str, bseries_id, value_id) -> bool:
        """Put a series that is still in retry-backoff back on the queue.

        Returns True when the caller must stop handling this queue value.

        Re-enqueueing sends the series to the BACK of the queue, so healthy
        series behind it are served immediately instead of waiting out its
        backoff. A queue that contains nothing BUT backing-off series would
        otherwise be a hot dequeue/re-enqueue loop, so after a few deferrals
        in a row the worker takes one idle sleep.
        """
        not_before = self._copy_retry_not_before.get(series_id)
        if not_before is None:
            return False

        remaining_sec = not_before - time.monotonic()
        if remaining_sec <= 0:
            self._copy_retry_not_before.pop(series_id, None)
            return False

        logger.debug("series still in copy backoff; re-queuing it behind the others",
                     series_id=series_id,
                     remaining_sec=round(remaining_sec, 1))
        try:
            orthanc.EnqueueValue(_COPY_QUEUE_NAME, bseries_id)
        except BaseException as e:
            # Leave the value reserved: its lease expires and Orthanc hands
            # it back. Do NOT acknowledge -- that would drop the series.
            self._log_copy_thread_exception(
                "failed to re-enqueue a backing-off series; leaving the queue value "
                "unacknowledged for lease release",
                e,
                series_id=series_id,
                value_id=str(value_id))
            return True

        self._acknowledge_copy_queue_value(value_id=value_id, series_id=series_id)

        self._consecutive_deferrals += 1
        if self._consecutive_deferrals >= _COPY_QUEUE_MAX_DEFERRALS_BEFORE_IDLE:
            self._consecutive_deferrals = 0
            time.sleep(_COPY_QUEUE_IDLE_SLEEP_SECONDS)
        return True


    def _acknowledge_copy_queue_value(self, value_id, series_id: str) -> bool:
        try:
            logger.debug("calling orthanc.AcknowledgeQueueValue()", series_id=series_id, value_id=str(value_id))
            orthanc.AcknowledgeQueueValue(_COPY_QUEUE_NAME, value_id)
            logger.debug("orthanc.AcknowledgeQueueValue() returned", series_id=series_id)
            return True
        except BaseException as e:
            self._log_copy_thread_exception("failed to acknowledge series-to-copy queue value; continuing",
                                            e,
                                            series_id=series_id,
                                            value_id=str(value_id))
            return False


    def copy_series_to_s3(self, series_id: str):
        logger.info("series copy to S3 starting", series_id=series_id)
        t0 = time.monotonic()

        # list all instances attachments
        attachments_uuids = self._get_instances_attachments(series_id=series_id)
        attachments_sizes = {}
        local_series_folder = None

        logger.debug("collected instance attachments for series",
                     series_id=series_id,
                     attachment_count=len(attachments_uuids))

        # Nothing to copy. The usual cause is that the series was deleted
        # between the enqueue and this dequeue, in which case /tools/find
        # returns no instances at all.
        #
        # This needs its own exit because BOTH fast paths below are guarded
        # by `if attachments_uuids`. Falling through with an empty list
        # builds an EMPTY zip, PUTs it to S3 under the series' key, and then
        # fails in _write_s3_uploaded_marker on the still-unset
        # local_series_folder -- so the series is re-enqueued and the whole
        # cycle repeats on every copy-queue backoff, forever, writing a junk
        # S3 object each time.
        if not attachments_uuids:
            logger.warning(
                "copy_series_to_s3: series has no supported attachment; nothing to copy "
                "(was it deleted after being enqueued?). Acknowledging without re-enqueueing.",
                series_id=series_id,
            )
            try:
                self._uncommitted_series_handler.on_committed_series(series_id=series_id)
            except Exception:
                logger.exception(
                    "copy_series_to_s3: failed to clear uncommitted-series KVS entry for a series "
                    "with no attachment; housekeeper will retry the cleanup",
                    series_id=series_id,
                )
            return

        # Dedup early-exit: the same series can be enqueued twice under
        # heavy ingest -- once by the natural STABLE_SERIES path, once
        # by the uncommitted-series housekeeper after the 5 min grace
        # period when the natural copy hasn't drained the queue yet.
        # The marker is the durable "folder contents match the S3 zip"
        # invariant (storage_create wipes it on every new instance), so
        # its presence is sufficient to skip a redundant rebuild + PUT
        # + per-attachment SetAttachmentCustomData round-trip.
        #
        # This check runs BEFORE the fast-path "data lost" guard below.
        # Otherwise an eviction between the first and second dequeue
        # (allowed precisely because the marker was written) would
        # purge the folder, the guard would see no local files, and we
        # would emit a misleading "data is lost" ERROR for a series
        # that is in fact safely on S3.
        if attachments_uuids:
            cached_folder = self._resolve_local_series_folder(attachments_uuids)
            if cached_folder:
                marker_path = os.path.join(
                    self._local_storage.get_folder_path(cached_folder),
                    S3_UPLOADED_MARKER_NAME,
                )
                with self._local_storage.folder_marker_critical_section(cached_folder):
                    if os.path.exists(marker_path):
                        logger.info(
                            "copy_series_to_s3: .s3-uploaded marker already present; "
                            "skipping redundant upload (duplicate enqueue)",
                            series_id=series_id,
                            local_series_folder=cached_folder,
                        )
                        try:
                            self._uncommitted_series_handler.on_committed_series(series_id=series_id)
                        except Exception:
                            logger.exception(
                                "copy_series_to_s3: failed to clear uncommitted-series KVS entry "
                                "on duplicate-enqueue skip; housekeeper will retry",
                                series_id=series_id,
                            )
                        return

        # Fast-path guard: nothing of this series is on local disk.
        #
        # That on its own is NOT a problem -- it is the healthy end state of
        # every series (uploaded, marker written, folder evicted). What
        # decides between "fine" and "lost" is whether EVERY attachment carries
        # an S3 zip key:
        #
        #   * all of them do -> the bytes are durable in S3. Rebuilding the zip
        #                       would download the whole series back into the
        #                       cache we just evicted, to re-upload
        #                       byte-identical content. Skip, quietly.
        #   * any of them do not -> those bytes are on no disk and in no zip.
        #                       Quarantine the series: recorded, reported, and
        #                       refused downstream. Without this exit the first
        #                       read_file would raise FileNotFoundError and the
        #                       worker would re-enqueue the same doomed series
        #                       for the life of the pod.
        #
        # The matching housekeeper pass detects the lost state and emits an
        # ERROR of its own; we log here too so a missed copy is visible even
        # without the housekeeper.
        #
        # TODO: when an Orthanc series-level metadata tag exists for
        # "data lost" (see s3_zip_storage._housekeep_one_uncommitted_series),
        # set it here. The housekeeper can then enumerate lost series via
        # a single /tools/find rather than walking logs.
        if not self._any_attachment_has_local_file(attachments_uuids):
            # Nothing on disk. That is either the healthiest state there is or
            # the worst one, and the difference is per attachment: an
            # attachment is recoverable if it carries an S3 zip key, and gone
            # if it does not. Asking "does ANY of them have a key?" is not the
            # same question -- a series where 78 attachments were uploaded and
            # the 79th never was would answer yes and be waved through as
            # "already on S3", which is precisely how a mutilated series would
            # slip past unnoticed. Only "are they ALL covered?" is safe, so we
            # pay for the full walk here, on the cold path.
            unrecoverable = self._collect_unrecoverable_attachments(attachments_uuids)
            if unrecoverable:
                self._quarantine_damaged_series(
                    series_id=series_id,
                    attachments_uuids=attachments_uuids,
                    unrecoverable_uuids=unrecoverable,
                    local_series_folder=self._resolve_local_series_folder(attachments_uuids),
                )
                return

            logger.info(
                "copy_series_to_s3: no local data left, but every attachment is backed by an "
                "S3 zip (folder evicted after a successful upload); nothing to copy",
                series_id=series_id,
                attachment_count=len(attachments_uuids),
            )
            try:
                self._uncommitted_series_handler.on_committed_series(series_id=series_id)
            except Exception:
                logger.exception(
                    "copy_series_to_s3: failed to clear uncommitted-series KVS entry "
                    "after abandoning; housekeeper will retry the cleanup",
                    series_id=series_id,
                )
            return

        total_uncompressed_bytes = 0
        zipped_uuids: List[str] = []
        # True only once the marker is published, i.e. once the folder is
        # provably covered by the zip we uploaded.
        series_fully_on_s3 = False

        # let's zip them in a temp file and upload it to S3.
        with tempfile.NamedTemporaryFile(delete=True, suffix=".zip") as tmp_zip:
            logger.debug("building zip archive",
                         series_id=series_id,
                         tmp_path=tmp_zip.name,
                         attachment_count=len(attachments_uuids))

            with ExitStack() as local_folder_lease:
                with zipfile.ZipFile(tmp_zip.name, "w", compression=self._zip_compression) as zipf:
                    for idx, a_uuid in enumerate(attachments_uuids):
                        if not local_series_folder: # they all share the same folder
                            local_series_folder = CustomData.from_orthanc_attachment(a_uuid).local_series_folder
                            local_folder_lease.enter_context(self._local_storage.lease_folder(local_series_folder))
                            logger.debug("resolved local_series_folder from first attachment",
                                         series_id=series_id,
                                         local_series_folder=local_series_folder)
                        try:
                            content = self._local_storage.read_file(uuid=a_uuid,
                                                                    local_series_folder=local_series_folder)
                        except FileNotFoundError:
                            # A series can legally reach this state: it was
                            # uploaded (folder marked), evicted, then NEW
                            # instances arrived and recreated the folder with
                            # only the new files -- the older attachments now
                            # exist ONLY inside the previous S3 zip. Rebuild
                            # the folder from that zip once, then retry.
                            # Retrieval will not republish the marker (folder
                            # contents != zip contents), so the folder stays
                            # eviction-protected until this re-upload lands.
                            try:
                                content = self._rehydrate_and_reread(
                                    series_id=series_id,
                                    a_uuid=a_uuid,
                                    local_series_folder=local_series_folder,
                                )
                            except FileNotFoundError:
                                # No local file and no zip that holds it: these
                                # bytes exist nowhere.
                                #
                                # Abandon the WHOLE series. Not "skip this
                                # attachment and upload the rest": an archive
                                # that silently omits an instance is the most
                                # dangerous artefact this plugin can produce,
                                # because every consumer downstream would treat
                                # it as the series. See _quarantine_damaged_series.
                                lost_uuids = self._collect_unrecoverable_attachments(
                                    attachments_uuids
                                ) or [a_uuid]
                                self._quarantine_damaged_series(
                                    series_id=series_id,
                                    attachments_uuids=attachments_uuids,
                                    unrecoverable_uuids=lost_uuids,
                                    local_series_folder=local_series_folder,
                                )
                                return
                        zipped_uuids.append(a_uuid)
                        attachments_sizes[a_uuid] = len(content)
                        total_uncompressed_bytes += attachments_sizes[a_uuid]
                        logger.debug("adding attachment to zip",
                                     series_id=series_id,
                                     uuid=a_uuid,
                                     index=idx,
                                     size_bytes=attachments_sizes[a_uuid])
                        zipf.writestr(a_uuid, content)
                        logger.debug("attachment added to zip",
                                     series_id=series_id,
                                     uuid=a_uuid,
                                     index=idx)

                t_zip_done = time.monotonic()
                zip_size_bytes = os.path.getsize(tmp_zip.name)

                if not zipped_uuids:
                    # Defensive: the read loop quarantines the series the moment
                    # an attachment turns out to be unrecoverable, so an empty
                    # zip should be unreachable. If it ever is reached, uploading
                    # would PUT an empty archive over this series' key and
                    # destroy a good one.
                    self._quarantine_damaged_series(
                        series_id=series_id,
                        attachments_uuids=attachments_uuids,
                        unrecoverable_uuids=self._collect_unrecoverable_attachments(attachments_uuids),
                        local_series_folder=local_series_folder,
                    )
                    return

                logger.info("zip archive built",
                            series_id=series_id,
                            attachment_count=len(zipped_uuids),
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

                # Update the custom data to notify that the file is now stored in a zip in S3.
                # Only for the attachments that ARE in the zip: an attachment we
                # could not read is not in there, and must keep its LOCAL custom
                # data so nothing downstream believes it is recoverable from S3.
                logger.info("starting SetAttachmentCustomData loop",
                            series_id=series_id,
                            attachment_count=len(zipped_uuids),
                            s3_key=s3_key)
                t_meta_start = time.monotonic()

                def set_attachment_custom_data(a_uuid: str, idx: int) -> None:
                    logger.debug("calling orthanc.SetAttachmentCustomData()",
                                 series_id=series_id,
                                 uuid=a_uuid,
                                 index=idx,
                                 total=len(zipped_uuids))

                    s3_custom_data = CustomData(storage=CustomData.Storage.S3_ZIP,
                                                local_series_folder=local_series_folder,
                                                s3_zip_key=s3_key,
                                                series_id=series_id,
                                                size_in_bytes=attachments_sizes[a_uuid]).to_binary()

                    orthanc.SetAttachmentCustomData(a_uuid, s3_custom_data)
                    logger.debug("orthanc.SetAttachmentCustomData() returned",
                                 series_id=series_id,
                                 uuid=a_uuid,
                                 index=idx)

                with ThreadPoolExecutor(max_workers=CUSTOM_DATA_CREATION_NUM_THREADS) as executor:
                    futures  = [
                        executor.submit(set_attachment_custom_data, a_uuid, idx)
                        for idx, a_uuid in enumerate(zipped_uuids)
                    ]

                    # Wait for all tasks to complete and propagate any exceptions
                    for future in futures:
                        future.result()

                t_meta_done = time.monotonic()
                logger.info("SetAttachmentCustomData loop complete",
                            series_id=series_id,
                            attachment_count=len(zipped_uuids),
                            s3_key=s3_key,
                            metadata_update_ms=int((t_meta_done - t_meta_start) * 1000))

                # Decide whether the folder may now be declared "recoverable
                # from S3", under the per-folder marker critical section.
                #
                # TWO independent conditions, because they catch different
                # things and only one of them is race-free on its own:
                #
                #   1. The DISK must hold nothing the zip does not have. This
                #      is the authoritative check. Orthanc records an
                #      attachment in its index only AFTER the storage area's
                #      Create returns, so a brand-new instance is on disk
                #      before /tools/find will admit it exists -- see
                #      _files_on_disk_not_in_zip for the full argument and for
                #      the CI failure that proved it.
                #
                #   2. Orthanc's attachment set must still match the snapshot
                #      we uploaded. Redundant with (1) for new instances, but
                #      it also catches an instance DELETED mid-copy, and it
                #      gives a much more readable log line.
                #
                # The critical section serializes against storage_create's
                # marker invalidation, so a write that lands after our listdir
                # is guaranteed to wipe the marker we just published rather
                # than interleave with it. The folder lease is still held here,
                # so eviction cannot remove the folder between the tmp-file
                # open in _write_s3_uploaded_marker step 1 and the atomic
                # os.replace to .s3-uploaded in step 2.
                if local_series_folder:
                    with self._local_storage.folder_marker_critical_section(local_series_folder):
                        current_attachments: list[str] = self._get_instances_attachments(series_id=series_id)
                        attachments_changed: bool = set(current_attachments) != set(attachments_uuids)
                        unzipped_files_on_disk: List[str] = self._files_on_disk_not_in_zip(
                            local_series_folder=local_series_folder,
                            zipped_uuids=set(zipped_uuids),
                        )

                        if not attachments_changed and not unzipped_files_on_disk:
                            self._write_s3_uploaded_marker(
                                local_series_folder=local_series_folder,
                                s3_key=s3_key,
                                series_id=series_id,
                            )
                            series_fully_on_s3 = True
                        else:
                            new_uuids = sorted(
                                set(current_attachments) - set(attachments_uuids)
                            )
                            dropped_uuids = sorted(
                                set(attachments_uuids) - set(current_attachments)
                            )
                            logger.warning(
                                msg="series folder holds data the uploaded zip does not cover; skipping marker write (next stable-series event will trigger a fresh copy)",
                                series_id=series_id,
                                s3_key=s3_key,
                                snapshot_count=len(attachments_uuids),
                                current_count=len(current_attachments),
                                zipped_count=len(zipped_uuids),
                                new_uuids=new_uuids,
                                dropped_uuids=dropped_uuids,
                                unzipped_files_on_disk=unzipped_files_on_disk[:20],
                            )

        duration_ms = int((time.monotonic() - t0) * 1000)

        # Clear the uncommitted-series bookkeeping only for a series that is
        # now fully on S3. When the marker was withheld, part of this series
        # is still local-only: a STABLE_SERIES event is expected to trigger
        # another copy, but that is an event we do not control, and dropping
        # the KVS entry here would also drop the housekeeper's safety net for
        # exactly the series that still needs it.
        if series_fully_on_s3:
            self._uncommitted_series_handler.on_committed_series(series_id=series_id)
            # Every attachment Orthanc lists was read and uploaded, so whatever
            # this series lost before has been made good -- typically by the
            # operator re-sending the study, which overwrites the empty records
            # (Orthanc runs with OverwriteInstances). Retract the alarm, or it
            # would keep the study blocked forever.
            self._clear_lost_attachments(series_id=series_id)
        else:
            logger.info("keeping the uncommitted-series entry: this copy did not cover the "
                        "whole folder, so the housekeeper stays responsible for it",
                        series_id=series_id)

        logger.info("series stored to S3",
                    series_id=series_id,
                    s3_key=s3_key,
                    bucket=self._bucket_name,
                    attachment_count=len(zipped_uuids),
                    zip_size_bytes=zip_size_bytes,
                    uncompressed_bytes=total_uncompressed_bytes,
                    zip_build_ms=int((t_zip_done - t0) * 1000),
                    upload_ms=int((t_upload_done - t_zip_done) * 1000),
                    metadata_update_ms=int((t_meta_done - t_meta_start) * 1000),
                    duration_ms=duration_ms)

    def _write_s3_uploaded_marker(self, local_series_folder: str, s3_key: str, series_id: str):
        folder_path = self._local_storage.get_folder_path(local_series_folder)
        marker_path = os.path.join(folder_path, S3_UPLOADED_MARKER_NAME)
        tmp_marker_path = os.path.join(
            folder_path,
            f"{S3_UPLOADED_MARKER_TMP_PREFIX}{os.getpid()}-{threading.get_ident()}"
        )

        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(tmp_marker_path, "w") as f:
                f.write(s3_key)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_marker_path, marker_path)
            self._fsync_directory_if_supported(folder_path)
            logger.debug("wrote S3 upload marker file",
                         series_id=series_id,
                         marker_path=marker_path,
                         s3_key=s3_key)
        except Exception as e:
            try:
                if os.path.exists(tmp_marker_path):
                    os.remove(tmp_marker_path)
            except Exception as cleanup_error:
                logger.warning("failed to remove temporary S3 upload marker",
                               series_id=series_id,
                               tmp_marker_path=tmp_marker_path,
                               error=str(cleanup_error))
            logger.warning("failed to write S3 upload marker file",
                           series_id=series_id,
                           marker_path=marker_path,
                           error=str(e))

    def invalidate_s3_uploaded_marker(self, local_series_folder: str) -> bool:
        """Remove the ``.s3-uploaded`` marker for ``local_series_folder``.

        Called on every storage_create for a series: any new instance landing
        on disk invalidates the marker's invariant ("everything in this folder
        is recoverable from S3"). Best effort -- a missing marker is the
        expected steady state.
        """
        folder_path = self._local_storage.get_folder_path(local_series_folder)
        marker_path = os.path.join(folder_path, S3_UPLOADED_MARKER_NAME)
        try:
            os.remove(marker_path)
            logger.debug("invalidated S3 upload marker",
                         local_series_folder=local_series_folder,
                         marker_path=marker_path)
            return True
        except FileNotFoundError:
            return False
        except OSError as e:
            logger.warning("failed to invalidate S3 upload marker",
                           local_series_folder=local_series_folder,
                           marker_path=marker_path,
                           error=str(e))
            return False

    def _fsync_directory_if_supported(self, folder_path: str):
        if not hasattr(os, "O_DIRECTORY"):
            return

        directory_fd = None
        try:
            directory_fd = os.open(folder_path, os.O_RDONLY | os.O_DIRECTORY)
            os.fsync(directory_fd)
        except OSError as e:
            logger.debug("directory fsync after marker write failed",
                         folder_path=folder_path,
                         error=str(e))
        finally:
            if directory_fd is not None:
                os.close(directory_fd)

    def _acquire_zip_retrieval(self, s3_zip_key: str) -> Tuple[ZipRetrieval, bool]:
        """Return the active retrieval object with a counted live reference.

        Lookup/create and refcount increment share the same lock. A thread must
        not leave this method with an uncounted object: if another thread
        completes the retrieval before this caller enters the condition, the
        active dictionary entry still has to stay alive for this caller.
        """
        with self._s3_zip_retrievals_lock:
            is_new_retrieval = False
            if s3_zip_key not in self._s3_zip_retrievals:
                self._s3_zip_retrievals[s3_zip_key] = LocalToS3ZipManager.ZipRetrieval(s3_zip_key)
                is_new_retrieval = True
            zip_retrieval = self._s3_zip_retrievals[s3_zip_key]
            zip_retrieval._ref_count += 1
            logger.debug("acquired ZipRetrieval",
                         s3_zip_key=s3_zip_key,
                         ref_count=zip_retrieval._ref_count,
                         is_new_retrieval=is_new_retrieval)
            return zip_retrieval, is_new_retrieval


    def _release_zip_retrieval(self, zip_retrieval: ZipRetrieval):
        """Release a counted retrieval reference and discard it when idle."""
        with self._s3_zip_retrievals_lock:
            zip_retrieval._ref_count -= 1
            logger.debug("released ZipRetrieval",
                         s3_zip_key=zip_retrieval.series_id,
                         ref_count=zip_retrieval._ref_count)
            if zip_retrieval._ref_count == 0:
                if self._s3_zip_retrievals.get(zip_retrieval.series_id) is zip_retrieval:
                    del self._s3_zip_retrievals[zip_retrieval.series_id]
                    logger.debug("discarded ZipRetrieval", s3_zip_key=zip_retrieval.series_id)
                else:
                    logger.warning("ZipRetrieval release found a different active retrieval",
                                   s3_zip_key=zip_retrieval.series_id)


    def get_s3_zip_stream(self, series_id: str):  # returns a stream
        logger.info("series zip stream from S3",
                    series_id=series_id)

        s3_zip_key = self._get_series_s3_key(series_id=series_id)

        response =  self._s3_client.get_object(Bucket=self._bucket_name,
                                               Key=s3_zip_key)
        return response['Body']


    def _rehydrate_and_reread(self, series_id: str, a_uuid: str, local_series_folder: str) -> bytes:
        """Restore a locally-missing attachment from the series' previous S3 zip.

        Called by ``copy_series_to_s3`` when an attachment file is absent from
        the local folder although Orthanc still lists it. That state is legal:
        the series was uploaded, its folder evicted, then new instances
        recreated the folder with only the new files. The missing bytes live
        in the previously-uploaded zip, referenced by the attachment's
        custom data. Raises FileNotFoundError if the attachment was never
        uploaded (no ``s3_zip_key``) -- in that case the data is really gone
        and the caller's failure path must handle it.
        """
        cd = CustomData.from_orthanc_attachment(a_uuid)
        s3_zip_key = cd.s3_zip_key if cd else None
        if not s3_zip_key:
            logger.error(
                "copy_series_to_s3: attachment file missing locally and never uploaded to S3; "
                "cannot rehydrate",
                series_id=series_id,
                uuid=a_uuid,
                local_series_folder=local_series_folder,
            )
            raise FileNotFoundError(
                f"attachment {a_uuid} of series {series_id} has no local file and no S3 zip"
            )

        logger.warning(
            "copy_series_to_s3: attachment file missing locally (folder evicted after a previous "
            "upload, then recreated by newer instances); rehydrating from the previous S3 zip",
            series_id=series_id,
            uuid=a_uuid,
            s3_zip_key=s3_zip_key,
            local_series_folder=local_series_folder,
        )
        self.retrieve_zip_from_s3(s3_zip_key=s3_zip_key,
                                  local_series_folder=local_series_folder)
        return self._local_storage.read_file(uuid=a_uuid,
                                             local_series_folder=local_series_folder)


    def retrieve_zip_from_s3(self, s3_zip_key: str, local_series_folder: str):
        # make sure we do not retrieve the same file multiple times at the same time
        zip_retrieval, is_new_retrieval = self._acquire_zip_retrieval(s3_zip_key)

        logger.debug("retrieve_zip_from_s3 entered",
                     s3_zip_key=s3_zip_key,
                     local_series_folder=local_series_folder,
                     is_new_retrieval=is_new_retrieval)

        try:
            # The zip is extracted as several file writes. A folder may already
            # contain an S3 marker from an earlier upload, so eviction must skip
            # it until the extraction and all waiters have left this retrieval.
            with self._local_storage.lease_folder(local_series_folder):
                with zip_retrieval: # the first thread to get here keeps the condition "locked" during the zip retrieval
                    zip_retrieval.raise_if_failed()
                    if not zip_retrieval.downloaded:
                        logger.debug("this thread will perform the S3 download",
                                     s3_zip_key=s3_zip_key)
                        try:
                            self._retrieve_zip_from_s3(s3_zip_key, local_series_folder)
                        except Exception as e:
                            zip_retrieval.set_failed(e)
                            raise
                        else:
                            zip_retrieval.set_downloaded()
                    else:
                        logger.debug("another thread already downloaded this zip, waiting",
                                     s3_zip_key=s3_zip_key)
                        zip_retrieval.wait_downloaded()
        finally:
            self._release_zip_retrieval(zip_retrieval)

    def delete_zip_from_s3(self, s3_zip_key: str):
        started_at = time.monotonic()
        for attempt in range(1, self._s3_retrieval_max_attempts + 1):
            try:
                self._s3_client.delete_object(Bucket=self._bucket_name,
                                              Key=s3_zip_key)
                logger.info(f"deleted zip from s3: {s3_zip_key}")
                return
            except Exception as e:
                retryable = self._is_retryable_s3_retrieval_exception(e)
                is_last_attempt = attempt >= self._s3_retrieval_max_attempts
                if not retryable or is_last_attempt:
                    logger.error(
                        "zip deletion from S3 failed",
                        s3_zip_key=s3_zip_key,
                        bucket=self._bucket_name,
                        attempt=attempt,
                        max_attempts=self._s3_retrieval_max_attempts,
                        retryable=retryable,
                        error_type=type(e).__name__,
                        error=str(e),
                        elapsed_ms=int((time.monotonic() - started_at) * 1000),
                    )
                    raise

                delay_sec = self._get_s3_retrieval_retry_delay_sec(attempt)
                logger.warning(
                    "zip deletion from S3 failed, retrying",
                    s3_zip_key=s3_zip_key,
                    bucket=self._bucket_name,
                    attempt=attempt,
                    max_attempts=self._s3_retrieval_max_attempts,
                    retry_delay_ms=int(delay_sec * 1000),
                    error_type=type(e).__name__,
                    error=str(e),
                )
                if delay_sec > 0:
                    time.sleep(delay_sec)

    def _retrieve_zip_from_s3(self, s3_zip_key: str, local_series_folder: str):
        started_at = time.monotonic()
        for attempt in range(1, self._s3_retrieval_max_attempts + 1):
            try:
                return self._retrieve_zip_from_s3_once(
                    s3_zip_key=s3_zip_key,
                    local_series_folder=local_series_folder,
                    attempt=attempt,
                )
            except Exception as e:
                retryable = self._is_retryable_s3_retrieval_exception(e)
                is_last_attempt = attempt >= self._s3_retrieval_max_attempts
                if not retryable or is_last_attempt:
                    logger.error(
                        "series retrieval from S3 failed",
                        s3_zip_key=s3_zip_key,
                        bucket=self._bucket_name,
                        local_series_folder=local_series_folder,
                        attempt=attempt,
                        max_attempts=self._s3_retrieval_max_attempts,
                        retryable=retryable,
                        error_type=type(e).__name__,
                        error=str(e),
                        elapsed_ms=int((time.monotonic() - started_at) * 1000),
                    )
                    raise

                delay_sec = self._get_s3_retrieval_retry_delay_sec(attempt)
                logger.warning(
                    "series retrieval from S3 failed, retrying",
                    s3_zip_key=s3_zip_key,
                    bucket=self._bucket_name,
                    local_series_folder=local_series_folder,
                    attempt=attempt,
                    max_attempts=self._s3_retrieval_max_attempts,
                    retry_delay_ms=int(delay_sec * 1000),
                    error_type=type(e).__name__,
                    error=str(e),
                )
                if delay_sec > 0:
                    time.sleep(delay_sec)

    def _retrieve_zip_from_s3_once(self, s3_zip_key: str, local_series_folder: str, attempt: int):
        logger.info("series retrieval from S3 starting",
                    s3_zip_key=s3_zip_key,
                    bucket=self._bucket_name,
                    local_series_folder=local_series_folder,
                    attempt=attempt,
                    max_attempts=self._s3_retrieval_max_attempts)
        t0 = time.monotonic()

        file_count = 0
        total_bytes = 0
        extracted_uuids: set[str] = set()

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
                        extracted_uuids.add(file_info.filename)
                        logger.debug("extracted file from zip to local storage",
                                     s3_zip_key=s3_zip_key,
                                     uuid=file_info.filename,
                                     size_bytes=len(content),
                                     index=file_count)

        # Publish the .s3-uploaded marker so the eviction guard and the
        # local-cache stats both reflect that this folder is recoverable
        # from S3 at s3_zip_key.
        #
        # The retrieve path is the second place (besides the copy thread)
        # that leaves a folder on disk whose contents fully match the S3 zip;
        # without this write the folder would be reported as "not yet on S3"
        # and protected from eviction forever even though the zip is durable.
        #
        # Race protection: the per-folder marker critical section serializes
        # against storage_create's invalidate path. Inside the section we
        # listdir the folder and only write the marker if its non-marker
        # contents equal exactly the set of uuids we just extracted.
        #
        # So that, if a concurrent storage_create wrote a new instance file
        # into this folder during retrieval, the extra file is visible and
        # we skip the marker (the next STABLE_SERIES copy will publish a marker
        # that reflects the new instance)
        #
        # The folder lease held by retrieve_zip_from_s3 keeps eviction out for
        # the whole window.

        folder_path: str = self._local_storage.get_folder_path(local_series_folder)
        with self._local_storage.folder_marker_critical_section(local_series_folder):
            try:
                on_disk = {
                    name for name in os.listdir(folder_path)
                    if name != S3_UPLOADED_MARKER_NAME
                    and not name.startswith(S3_UPLOADED_MARKER_TMP_PREFIX)
                }
            except FileNotFoundError:
                on_disk = None

            if on_disk == extracted_uuids:
                self._write_s3_uploaded_marker(
                    local_series_folder=local_series_folder,
                    s3_key=s3_zip_key,
                    series_id=local_series_folder,
                )
            else:
                # Handle the situation where the series has been modified during retrieval.

                logger.info(
                    "retrieve: folder contents differ from zip; skipping marker write "
                    "(a concurrent storage_create likely added an instance during retrieval)",
                    s3_zip_key=s3_zip_key,
                    local_series_folder=local_series_folder,
                    extracted_count=len(extracted_uuids),
                    on_disk_count=(None if on_disk is None else len(on_disk)),
                )

        duration_ms = int((time.monotonic() - t0) * 1000)

        logger.info("series retrieved from S3",
                    s3_zip_key=s3_zip_key,
                    bucket=self._bucket_name,
                    local_series_folder=local_series_folder,
                    attempt=attempt,
                    file_count=file_count,
                    zip_size_bytes=zip_size_bytes,
                    uncompressed_bytes=total_bytes,
                    download_ms=int((t_download_done - t0) * 1000),
                    duration_ms=duration_ms)

    def _get_s3_retrieval_retry_delay_sec(self, failed_attempt: int) -> float:
        if self._s3_retrieval_retry_base_delay_sec <= 0:
            return 0.0

        exponential_delay = self._s3_retrieval_retry_base_delay_sec * (2 ** max(0, failed_attempt - 1))
        capped_delay = min(exponential_delay, self._s3_retrieval_retry_max_delay_sec)
        return random.uniform(0.0, capped_delay)

    def _is_retryable_s3_retrieval_exception(self, exc: BaseException) -> bool:
        if isinstance(exc, zipfile.BadZipFile):
            return False

        if ClientError is not None and isinstance(exc, ClientError):
            response = getattr(exc, "response", {}) or {}
            error = response.get("Error", {}) or {}
            metadata = response.get("ResponseMetadata", {}) or {}
            error_code = error.get("Code")
            http_status_code = metadata.get("HTTPStatusCode")
            if error_code in _PERMANENT_CLIENT_ERROR_CODES:
                return False
            if error_code in _TRANSIENT_CLIENT_ERROR_CODES:
                return True
            if http_status_code in _TRANSIENT_HTTP_STATUS_CODES:
                return True
            return False

        if _TRANSIENT_BOTOCORE_EXCEPTIONS and isinstance(exc, _TRANSIENT_BOTOCORE_EXCEPTIONS):
            return True

        if isinstance(exc, (ConnectionError, TimeoutError)):
            return True

        return False


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

    def _record_lost_attachments(self, series_id: str, lost_uuids: List[str]) -> bool:
        """Record destroyed attachments in a durable, listable place.

        Returns whether the record was written. The caller cares: this entry is
        what the per-series status endpoint reads, and therefore what makes the
        Gap Server refuse to process the study. A loss that is only in a log
        line is a loss nobody acts on, so a failed write must not be shrugged
        off -- see _quarantine_damaged_series.
        """
        try:
            payload = json.dumps({
                "series_id": series_id,
                "lost_attachment_count": len(lost_uuids),
                # Capped: the point is to identify the series, not to mirror a
                # 10k-instance attachment list into the KVS.
                "lost_uuids": lost_uuids[:100],
                "detected_at_epoch_ms": int(time.time() * 1000),
            }).encode("utf-8")
            orthanc.StoreKeyValue(LOST_DATA_KVS, series_id, payload)
            return True
        except Exception:
            logger.exception(
                "could not record the lost-data marker for this series; the loss is only in "
                "the log until this succeeds",
                series_id=series_id,
            )
            return False

    def _clear_lost_attachments(self, series_id: str) -> None:
        """Retract the lost-data record for a series that is now complete on S3.

        Best effort in the other direction: a stale entry keeps the Gap Server
        refusing a study that has since been repaired, so it is worth clearing,
        but failing to clear it cannot make anything unsafe.
        """
        try:
            if not orthanc.GetKeyValue(LOST_DATA_KVS, series_id):
                return
        except Exception:
            return

        try:
            orthanc.DeleteKeyValue(LOST_DATA_KVS, series_id)
            logger.warning(
                "series previously reported as having lost instances is now fully uploaded to "
                "S3; clearing its lost-data record (it was presumably re-sent)",
                series_id=series_id,
            )
        except Exception:
            logger.exception(
                "could not clear the lost-data record of a repaired series; the study stays "
                "blocked until it is removed",
                series_id=series_id,
            )

    def get_lost_attachment_count(self, series_id: str) -> int:
        """How many of this series' attachments are known to be destroyed."""
        try:
            raw = orthanc.GetKeyValue(LOST_DATA_KVS, series_id)
        except Exception:
            return 0
        if not raw:
            return 0
        try:
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8")
            return int(json.loads(raw).get("lost_attachment_count", 0))
        except Exception:
            # An entry we cannot parse still means "this series lost data".
            return 1

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

        # One attachment's custom data cannot speak for the series: an
        # attachment whose bytes were destroyed keeps LOCAL custom data while
        # every other attachment moves to S3_ZIP, so sampling attachments[0]
        # reports a mutilated series as fully stored. The lost-data KVS is the
        # O(1) answer to the part sampling cannot see.
        status.lost_attachment_count = self.get_lost_attachment_count(series_id=series_id)

        return status
