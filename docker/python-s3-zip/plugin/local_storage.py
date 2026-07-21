from __future__ import annotations

import logging
import os
import orthanc
import sys
import threading
import subprocess
import time
import queue
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Dict, Iterator, List, Optional, Tuple
from local_storage_interface import LocalStorageInterface
from collections import deque
from s3zip_logging import get_logger

FolderStatEntry = Tuple[float, str, int]


@dataclass
class EvictionResult:
    """Outcome of an eviction pass.

    Returned both by the make-room slow path and by the explicit
    ``evict_all_safe`` admin entry point so callers (REST endpoint, CI tests,
    health page) can render uniform stats.
    """
    freed_folders: int
    freed_bytes: int
    skipped_folders: int
    available_bytes_after: int

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Per-module log-level override for eviction / disk-space monitoring.
#
# S3ZIP_LOCAL_STORAGE_LOG_LEVEL overrides the level for the s3zip.local_storage
# logger only, without affecting any other s3zip.* module.  This makes it easy
# to enable verbose eviction tracing in CI without flooding the logs with
# debug output from upload/download/read paths.
#
# Accepted values: DEBUG, INFO, WARNING, ERROR (case-insensitive).
# If unset, the level is inherited from the parent s3zip logger
# (controlled by S3ZIP_LOG_LEVEL, default INFO).
#
# Example (CI compose file):
#   S3ZIP_LOCAL_STORAGE_LOG_LEVEL: DEBUG
# ---------------------------------------------------------------------------
_LOCAL_STORAGE_LOG_LEVEL_ENV_VAR = "S3ZIP_LOCAL_STORAGE_LOG_LEVEL"
_module_level_override: Optional[str] = os.environ.get(_LOCAL_STORAGE_LOG_LEVEL_ENV_VAR)
if _module_level_override:
    _lvl: Any = getattr(logging, _module_level_override.upper(), None)
    if _lvl is not None:
        # Set the level on this module's logger so isEnabledFor() returns True for
        # records at the override level.
        logger.setLevel(_lvl)
        # Also lower the level on any handler attached directly to the s3zip root logger
        # (the one installed by _ensure_s3zip_logging before inject_logger_factory is
        # called).  Without this, Python's callHandlers() would filter the record at the
        # handler even though the originating logger accepted it — the handler-level check
        # is independent of the logger-level check and is the one that matters during
        # propagation.  After inject_logger_factory() the s3zip root handler is removed
        # and replaced by the root-logger handler (level=NOTSET=0), so this adjustment is
        # only relevant during the import-time window and in standalone setups that never
        # call inject_logger_factory().
        _s3zip_root: logging.Logger = logging.getLogger("s3zip")
        for _h in _s3zip_root.handlers:
            if _lvl < _h.level:
                _h.setLevel(_lvl)
        print(
            f"[s3zip] local_storage: log level overridden by "
            f"{_LOCAL_STORAGE_LOG_LEVEL_ENV_VAR}={_module_level_override.upper()}",
            file=sys.stderr,
        )
    else:
        print(
            f"[s3zip] local_storage: ignoring invalid "
            f"{_LOCAL_STORAGE_LOG_LEVEL_ENV_VAR}={_module_level_override!r}",
            file=sys.stderr,
        )


# du(1) exits non-zero (typically 1) when it cannot stat an entry — e.g. a
# series folder is evicted/removed by another thread while du is walking the
# cache. In that case du still prints valid sizes for every surviving entry on
# stdout, so a partial result is safe to use. A run that produces NO usable
# output at all is treated as transient and retried with exponential backoff.
_DU_MAX_ATTEMPTS: int = 3
_DU_RETRY_BACKOFF_BASE_SEC: float = 0.1


class LocalStorage(LocalStorageInterface):


    _root: str
    _max_size: int    # all sizes are in [bytes]
    _available_size: int
    _block_size: int
    _lock: threading.RLock
    _io_condition: threading.Condition
    _active_writers: int
    _scan_in_progress: bool
    _reserved_bytes: int
    _folder_lease_counts: dict[str, int]
    _folder_marker_cs_locks: dict[str, tuple[threading.Lock, int]]
    _folder_stats: queue.PriorityQueue[FolderStatEntry]
    _is_folder_safe_to_evict: Callable[[str], bool] | None

    def __init__(self, root: str, max_size_mb: int) -> None:
        self._root = root
        self._max_size = max_size_mb * 1024 * 1024
        self._lock = threading.RLock()
        self._io_condition = threading.Condition()
        self._active_writers = 0
        self._scan_in_progress = False
        self._reserved_bytes = 0
        self._folder_lease_counts = {}
        self._folder_marker_cs_locks = {}
        self._is_folder_safe_to_evict = None

        self._update_local_storage_stats()

        logger.debug("LocalStorage initialized",
                     root=root,
                     max_size_mb=max_size_mb,
                     max_size_bytes=self._max_size)

    def set_eviction_guard(self, is_folder_safe_to_evict: Callable[[str], bool]) -> None:
        """
        - Set a callback that determines if a local series folder is safe to evict.
        - The callback receives the folder name (not the full path) and
          must return True if the folder's data has been safely backed up to S3.
        - If this callback is not set, all folders are considered safe to evict.
        """
        self._is_folder_safe_to_evict = is_folder_safe_to_evict

    @contextmanager
    def lease_folder(self, local_series_folder: str) -> Iterator[None]:
        """Keep a series folder stable while a caller depends on its contents.

        Eviction removes whole series folders. A caller that checks a file path
        and then opens it, or extracts several files into the same folder, needs
        the folder to remain present for the full operation rather than only for
        one filesystem call. The lease is a refcount checked by eviction; it is
        not a global I/O mutex.
        """
        self._acquire_folder_lease(local_series_folder)
        try:
            yield
        finally:
            self._release_folder_lease(local_series_folder)

    def _acquire_folder_lease(self, local_series_folder: str) -> None:
        with self._lock:
            self._folder_lease_counts[local_series_folder] = (
                self._folder_lease_counts.get(local_series_folder, 0) + 1
            )
            logger.debug(
                "LocalStorage: folder lease acquired",
                local_series_folder=local_series_folder,
                lease_count=self._folder_lease_counts[local_series_folder],
            )

    def _release_folder_lease(self, local_series_folder: str) -> None:
        with self._lock:
            lease_count = self._folder_lease_counts.get(local_series_folder, 0)
            if lease_count <= 1:
                self._folder_lease_counts.pop(local_series_folder, None)
                lease_count = 0
            else:
                lease_count -= 1
                self._folder_lease_counts[local_series_folder] = lease_count
            logger.debug(
                "LocalStorage: folder lease released",
                local_series_folder=local_series_folder,
                lease_count=lease_count,
            )

    def _get_folder_lease_count(self, local_series_folder: str) -> int:
        return self._folder_lease_counts.get(local_series_folder, 0)

    @contextmanager
    def folder_marker_critical_section(self, local_series_folder: str) -> Iterator[None]:
        """Per-folder mutex for marker publish/invalidate operations.

        Two paths race for the marker file: ``copy_series_to_s3`` writes it
        after a final attachment-set recheck, and ``storage_create`` deletes
        it whenever a new instance lands on disk. Without serialization, the
        copy can publish a marker AFTER the create's delete has already run
        as a no-op, leaving a stale marker that hides an un-uploaded file.

        Acquiring is refcounted: the underlying ``threading.Lock`` is created
        lazily on first use and removed from the dict when no thread is in
        the section, so memory does not grow with the lifetime catalogue of
        series folders.
        """
        lock = self._acquire_folder_marker_cs(local_series_folder)
        try:
            with lock:
                yield
        finally:
            self._release_folder_marker_cs(local_series_folder)

    def _acquire_folder_marker_cs(self, local_series_folder: str) -> threading.Lock:
        with self._lock:
            entry = self._folder_marker_cs_locks.get(local_series_folder)
            if entry is None:
                new_lock = threading.Lock()
                self._folder_marker_cs_locks[local_series_folder] = (new_lock, 1)
                return new_lock
            existing_lock, count = entry
            self._folder_marker_cs_locks[local_series_folder] = (existing_lock, count + 1)
            return existing_lock

    def _release_folder_marker_cs(self, local_series_folder: str) -> None:
        with self._lock:
            entry = self._folder_marker_cs_locks.get(local_series_folder)
            if entry is None:
                return
            existing_lock, count = entry
            if count <= 1:
                del self._folder_marker_cs_locks[local_series_folder]
            else:
                self._folder_marker_cs_locks[local_series_folder] = (existing_lock, count - 1)

    def _update_local_storage_stats(self) -> None:
        self._pause_writes_for_scan()
        try:
            self._update_local_storage_stats_with_writes_paused()
        finally:
            self._resume_writes_after_scan()

    def _pause_writes_for_scan(self) -> None:
        # A scan must not overlap physical writes: otherwise `du` can see a
        # finished write while the reservation still counts it as in-flight.
        with self._io_condition:
            while self._scan_in_progress:
                self._io_condition.wait()
            self._scan_in_progress = True
            # If wait() is interrupted (e.g. by a signal) after we have already
            # claimed the scan slot, we must clear the flag and wake any other
            # blocked threads. Otherwise _scan_in_progress stays True forever
            # and every subsequent _enter_write / scan-pauser deadlocks.
            try:
                while self._active_writers > 0:
                    self._io_condition.wait()
            except BaseException:
                self._scan_in_progress = False
                self._io_condition.notify_all()
                raise

    def _resume_writes_after_scan(self) -> None:
        with self._io_condition:
            self._scan_in_progress = False
            self._io_condition.notify_all()

    def _enter_write(self) -> None:
        with self._io_condition:
            while self._scan_in_progress:
                self._io_condition.wait()
            self._active_writers += 1

    def _exit_write(self) -> None:
        with self._io_condition:
            self._active_writers -= 1
            if self._active_writers == 0:
                self._io_condition.notify_all()

    def _run_du_capture(self, cmd: List[str]) -> str:
        """Run ``du`` and return its stdout, hardened against the local cache
        mutating mid-scan.

        ``du`` exits non-zero when it fails to stat an entry — e.g. a series
        folder is evicted/removed by another thread while ``du`` walks the
        cache. When that happens ``du`` still prints valid sizes for every
        surviving entry on stdout, so we accept that partial output instead of
        letting a ``CalledProcessError`` crash the caller: the missing folders
        are exactly the ones being removed, so under-counting their bytes is
        self-correcting and gets picked up on the next scan. A run that yields
        no usable output at all is treated as transient (e.g. an ``ENOMEM``
        fork failure under load) and retried with exponential backoff before
        finally giving up.
        """
        last_stderr: str = ""
        for attempt in range(1, _DU_MAX_ATTEMPTS + 1):
            result: subprocess.CompletedProcess[str] = subprocess.run(
                cmd, capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout

            last_stderr = (result.stderr or "").strip()
            if result.stdout.strip():
                logger.warning(
                    "du exited non-zero but produced usable output; treating it as a partial scan (cache mutated mid-walk)",
                    returncode=result.returncode,
                    attempt=attempt,
                    stderr=last_stderr[:500],
                )
                return result.stdout

            logger.warning(
                "du produced no usable output; will retry with backoff",
                returncode=result.returncode,
                attempt=attempt,
                max_attempts=_DU_MAX_ATTEMPTS,
                stderr=last_stderr[:500],
            )
            if attempt < _DU_MAX_ATTEMPTS:
                backoff_sec: float = _DU_RETRY_BACKOFF_BASE_SEC * (1 << (attempt - 1))
                time.sleep(backoff_sec)

        raise RuntimeError(
            f"du failed to produce usable output after {_DU_MAX_ATTEMPTS} attempts for command {cmd!r}; last stderr: {last_stderr[:500]!r}"
        )

    def _update_local_storage_stats_with_writes_paused(self) -> None:
        block_size: int = os.statvfs(self._root).f_frsize
        folder_stats: queue.PriorityQueue[FolderStatEntry] = queue.PriorityQueue()

        cmd: List[str] = ["du", "-b", "--max-depth=1", self._root]
        du_stdout: str = self._run_du_capture(cmd)
        lines: List[str] = du_stdout.strip().split("\n")

        total_folders: int = 0
        total_apparent_bytes: int = 0
        for line in lines:
            if "\t" not in line:
                # Defensive: du emits complete "<size>\t<path>" lines, but a
                # mutating-cache scan is exactly when we must not trust that a
                # blank/partial line never sneaks in.
                continue
            size_str, path = line.split("\t", 1)
            folder_size: int = int(size_str)
            if path != self._root:
                last_modified: float = os.path.getmtime(path)
                folder_stats.put((last_modified, path, folder_size))
                total_folders += 1
                total_apparent_bytes += folder_size

        with self._lock:
            prev_available: Optional[int] = getattr(self, '_available_size', None)
            self._block_size = block_size
            self._folder_stats = folder_stats
            self._available_size = self._max_size - total_apparent_bytes - self._reserved_bytes

            logger.debug(
                "LocalStorage: disk stats refreshed",
                max_size_mb=self._max_size // (1024 * 1024),
                max_size_bytes=self._max_size,
                block_size=self._block_size,
                total_folders=total_folders,
                total_apparent_bytes=total_apparent_bytes,
                total_apparent_mb=round(total_apparent_bytes / (1024 * 1024), 2),
                reserved_bytes=self._reserved_bytes,
                reserved_mb=round(self._reserved_bytes / (1024 * 1024), 2),
                available_bytes=self._available_size,
                available_mb=round(self._available_size / (1024 * 1024), 2),
                prev_available_bytes=prev_available,
            )


    def _evict_until(self, target_available_bytes: Optional[int]) -> EvictionResult:
        """Evict oldest-first folders until ``self._available_size`` reaches the target.

        Caller MUST hold ``self._lock`` and MUST have paused writes via
        ``_pause_writes_for_scan``. Caller also MUST have refreshed
        ``self._folder_stats`` (e.g. via ``_update_local_storage_stats``)
        before calling: this method neither acquires the lock nor refreshes
        the queue.

        Args:
            target_available_bytes: stop the loop as soon as
                ``self._available_size >= target_available_bytes``. Pass
                ``None`` to drain the LRU queue completely (i.e. evict
                everything that the eviction guard considers safe to evict).

        Folders with active leases are skipped because another thread is using
        their contents across multiple filesystem calls. Folders without a
        ``.s3-uploaded`` marker are protected by the eviction guard set via
        ``set_eviction_guard``. Skipped folders are put back into the queue so
        they remain candidates for future eviction.
        """
        skipped: List[FolderStatEntry] = []
        freed_bytes: int = 0
        freed_folders: int = 0

        def _need_more() -> bool:
            if target_available_bytes is None:
                return True
            return self._available_size < target_available_bytes

        while _need_more() and not self._folder_stats.empty():
            entry: FolderStatEntry = self._folder_stats.get()
            _, path, folder_size = entry

            folder_name: str = os.path.basename(path)
            lease_count = self._get_folder_lease_count(folder_name)
            if lease_count > 0:
                logger.info(
                    "LocalStorage: skipping eviction of leased folder",
                    folder=folder_name,
                    folder_size=folder_size,
                    lease_count=lease_count)
                skipped.append(entry)
                continue

            if self._is_folder_safe_to_evict is not None:
                try:
                    safe = self._is_folder_safe_to_evict(folder_name)
                except Exception as e:
                    logger.warning("eviction guard check failed, skipping folder",
                                   folder=folder_name, error=str(e))
                    safe = False

                if not safe:
                    logger.info(
                        "LocalStorage: skipping eviction of folder not yet on S3",
                        folder=folder_name, folder_size=folder_size)
                    skipped.append(entry)
                    continue

            orthanc.LogInfo(f"LocalStorage: reclaiming space by deleting local folder '{path}'")
            logger.debug(
                "LocalStorage: evicting folder",
                folder=folder_name,
                folder_size=folder_size,
                available_before=self._available_size,
            )

            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                logger.info(
                    "LocalStorage: folder already gone during eviction",
                    folder=folder_name,
                    folder_size=folder_size,
                )
            except OSError as e:
                logger.warning(
                    "LocalStorage: failed to evict folder, leaving it queued for a future pass",
                    folder=folder_name,
                    folder_size=folder_size,
                    error=str(e),
                )
                skipped.append(entry)
                continue
            self._available_size += folder_size
            freed_bytes += folder_size
            freed_folders += 1

            logger.debug(
                "LocalStorage: folder evicted",
                folder=folder_name,
                folder_size=folder_size,
                available_after=self._available_size,
            )

        # put skipped entries back
        for entry in skipped:
            self._folder_stats.put(entry)

        return EvictionResult(
            freed_folders=freed_folders,
            freed_bytes=freed_bytes,
            skipped_folders=len(skipped),
            available_bytes_after=self._available_size,
        )

    def _make_room(self, size: int) -> int:
        reservation_size: int = max(size, 0)

        with self._lock:
            self._available_size -= reservation_size
            self._reserved_bytes += reservation_size

            logger.debug(
                "LocalStorage: _make_room called",
                requested_bytes=size,
                reservation_bytes=reservation_size,
                reserved_bytes=self._reserved_bytes,
                current_available_bytes=self._available_size,
                current_available_mb=round(self._available_size / (1024 * 1024), 2),
            )

            if self._available_size >= 0:
                logger.debug(
                    "LocalStorage: fast path - sufficient space, no eviction needed",
                    available_after_bytes=self._available_size,
                    available_after_mb=round(self._available_size / (1024 * 1024), 2),
                    reserved_bytes=self._reserved_bytes,
                )
                return reservation_size

            logger.debug(
                "LocalStorage: slow path - available space insufficient, refreshing disk stats",
                reservation_bytes=reservation_size,
                available_before_refresh_bytes=self._available_size,
                reserved_bytes=self._reserved_bytes,
            )

        scan_paused = False
        try:
            self._pause_writes_for_scan()
            scan_paused = True
            self._update_local_storage_stats_with_writes_paused()

            logger.debug(
                "LocalStorage: disk stats refreshed, starting eviction loop",
                reservation_bytes=reservation_size,
            )

            with self._lock:
                logger.debug(
                    "LocalStorage: starting eviction loop",
                    reservation_bytes=reservation_size,
                    available_after_refresh_bytes=self._available_size,
                    reserved_bytes=self._reserved_bytes,
                    folders_queued=self._folder_stats.qsize(),
                )

                # Reclaim space -- evict oldest folders first, but protect folders
                # whose data has not yet been safely backed up to S3.
                # This can be useful if the plugin receives a burst of uploads that
                # exceed the local storage capacity, but the S3 upload process is
                # still catching up
                result = self._evict_until(target_available_bytes=0)

                logger.debug(
                    "LocalStorage: eviction loop complete",
                    freed_folders=result.freed_folders,
                    freed_bytes=result.freed_bytes,
                    skipped_folders=result.skipped_folders,
                    reservation_bytes=reservation_size,
                    reserved_bytes=self._reserved_bytes,
                    available_after_eviction_bytes=self._available_size,
                    available_after_eviction_mb=round(self._available_size / (1024 * 1024), 2),
                )

                if self._available_size < 0:
                    logger.warning(
                        "LocalStorage: could not free enough space. "
                        "Some folders are protected because they are not yet on S3.",
                        needed=-self._available_size,
                        available=self._available_size,
                        available_mb=round(self._available_size / (1024 * 1024), 2),
                        reserved_bytes=self._reserved_bytes,
                        protected_folders=result.skipped_folders,
                        max_size_mb=self._max_size // (1024 * 1024),
                    )
        except Exception:
            self._rollback_write_reservation(reservation_size)
            raise
        finally:
            if scan_paused:
                self._resume_writes_after_scan()

        return reservation_size

    def _commit_write_reservation(self, reserved_bytes: int) -> None:
        if reserved_bytes <= 0:
            return

        with self._lock:
            self._reserved_bytes = max(0, self._reserved_bytes - reserved_bytes)
            logger.debug(
                "LocalStorage: write reservation committed",
                released_reserved_bytes=reserved_bytes,
                reserved_bytes=self._reserved_bytes,
                available_bytes=self._available_size,
            )

    def _rollback_write_reservation(self, reserved_bytes: int) -> None:
        if reserved_bytes <= 0:
            return

        with self._lock:
            self._reserved_bytes = max(0, self._reserved_bytes - reserved_bytes)
            self._available_size += reserved_bytes

    def _touch_lru_reference(self, folder_path: str) -> None:
        try:
            os.utime(folder_path, None)
        except OSError as e:
            logger.debug(
                "LocalStorage: failed to update folder LRU timestamp",
                folder=folder_path,
                error=str(e),
            )

    def evict_all_safe(self) -> EvictionResult:
        """Force-evict every locally-cached series that has been safely uploaded to S3.

        Admin/diagnostic entry point. Refreshes the LRU queue from disk, then
        drains it: every folder whose eviction guard returns True
        (``.s3-uploaded`` marker present) is removed from the local cache;
        folders still in flight are skipped and remain on disk.

        Synchronous: pauses concurrent ``write_file`` disk writes during the
        scan/eviction pass. The cost is O(num_local_folders) ``shutil.rmtree``
        calls plus one
        ``du -b --max-depth=1`` invocation.

        Returns an ``EvictionResult`` describing what was freed.
        """
        self._pause_writes_for_scan()
        try:
            self._update_local_storage_stats_with_writes_paused()
            with self._lock:
                result = self._evict_until(target_available_bytes=None)

                logger.info(
                    "LocalStorage: evict_all_safe complete",
                    freed_folders=result.freed_folders,
                    freed_bytes=result.freed_bytes,
                    skipped_folders=result.skipped_folders,
                    available_after_bytes=self._available_size,
                    available_after_mb=round(self._available_size / (1024 * 1024), 2),
                    reserved_bytes=self._reserved_bytes,
                )
                return result
        finally:
            self._resume_writes_after_scan()

    def get_cache_summary(self, marker_filename: str = ".s3-uploaded") -> Dict[str, int]:
        """Return a snapshot of local-cache occupancy.

        Refreshes the disk stats (does NOT evict) and walks the temp folder
        once to count how many series are already on S3 (i.e. have the
        ``marker_filename`` sentinel) versus still in flight.

        The counts are advisory — they are racy with the upload thread.
        """
        self._pause_writes_for_scan()
        try:
            self._update_local_storage_stats_with_writes_paused()
            uploaded: int = 0
            pending: int = 0
            try:
                for name in os.listdir(self._root):
                    folder: str = os.path.join(self._root, name)
                    if not os.path.isdir(folder):
                        continue
                    if os.path.exists(os.path.join(folder, marker_filename)):
                        uploaded += 1
                    else:
                        pending += 1
            except FileNotFoundError:
                pass
            with self._lock:
                total_folders: int = self._folder_stats.qsize()
                used_bytes: int = self._max_size - self._available_size
                return {
                    "max_bytes": self._max_size,
                    "available_bytes": self._available_size,
                    "used_bytes": used_bytes,
                    "reserved_bytes": self._reserved_bytes,
                    "total_folders": total_folders,
                    "folders_on_s3": uploaded,
                    "folders_not_on_s3": pending,
                }
        finally:
            self._resume_writes_after_scan()


    def write_file(self, local_series_folder: str, uuid: str, content: bytes) -> None:
        reserved_bytes: int = self._make_room(len(content))
        write_failed: bool = False

        self._enter_write()
        try:
            try:
                self._write_file(uuid=uuid,
                                 local_series_folder=local_series_folder,
                                 content_type=orthanc.ContentType.DICOM,
                                 content=content)
            except Exception:
                write_failed = True
                self._rollback_write_reservation(reserved_bytes)
                raise
            else:
                self._commit_write_reservation(reserved_bytes)
        finally:
            self._exit_write()
            if write_failed:
                try:
                    self._update_local_storage_stats()
                except Exception as e:
                    logger.warning(
                        "LocalStorage: failed to refresh stats after write failure; restored reservation optimistically",
                        released_reserved_bytes=reserved_bytes,
                        error=str(e),
                    )


    def _write_file(self, uuid: str, local_series_folder: str, content_type: orthanc.ContentType, content: bytes) -> None:

        path: str = self.get_local_path(uuid=uuid,
                                        local_series_folder=local_series_folder,
                                        content_type=content_type)

        logger.debug("writing file to local storage",
                     uuid=uuid,
                     local_series_folder=local_series_folder,
                     path=path,
                     size_bytes=len(content))

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "wb") as f:
            f.write(content)

        self._touch_lru_reference(os.path.dirname(path))

        logger.debug("file written to local storage",
                     uuid=uuid,
                     path=path,
                     size_bytes=len(content))

    def read_file(self, uuid: str, local_series_folder: str) -> bytes:

        return self._read_file(uuid=uuid,
                               local_series_folder=local_series_folder,
                               content_type=orthanc.ContentType.DICOM,
                               range_start=0,
                               size=0)

    def _read_file(self,
                   uuid: str,
                   local_series_folder: str,
                   content_type: orthanc.ContentType,
                   range_start: int,
                   size: int) -> bytes:

        path: str = self.get_local_path(uuid=uuid,
                                        local_series_folder=local_series_folder,
                                        content_type=content_type)

        logger.debug("reading file from local storage",
                     uuid=uuid,
                     path=path,
                     range_start=range_start,
                     requested_size=size)

        with open(path, "rb") as f:
            if range_start > 0:
                f.seek(range_start)

            if size > 0:
                data: bytes = f.read(size)
            else:
                data = f.read()

        logger.debug("file read from local storage",
                     uuid=uuid,
                     path=path,
                     bytes_read=len(data),
                     range_start=range_start)
        return data


    SUPPORTED_CONTENT_TYPES: ClassVar[Tuple[orthanc.ContentType, ...]] = (orthanc.ContentType.DICOM, orthanc.ContentType.DICOM_UNTIL_PIXEL_DATA)

    def create(self,
               uuid: str,
               local_series_folder: str,
               content_type: orthanc.ContentType,
               compression_type: orthanc.CompressionType,
               content: bytes) -> orthanc.ErrorCode:

        if content_type not in self.SUPPORTED_CONTENT_TYPES:
            raise RuntimeError(f"Unsupported content type: {content_type}")

        logger.debug("create called",
                     uuid=uuid,
                     local_series_folder=local_series_folder,
                     content_type=str(content_type),
                     size_bytes=len(content))

        try:
            self.write_file(uuid=uuid,
                            local_series_folder=local_series_folder,
                            content=content)

            logger.debug("create succeeded", uuid=uuid, local_series_folder=local_series_folder)
            return orthanc.ErrorCode.SUCCESS
        except IOError as e:
            logger.error("IO error creating local storage file",
                         uuid=uuid,
                         local_series_folder=local_series_folder,
                         error=str(e))
            return orthanc.ErrorCode.PLUGIN
        except Exception as e:
            logger.error("unexpected error creating local storage file",
                         uuid=uuid,
                         local_series_folder=local_series_folder,
                         error=str(e))
            return orthanc.ErrorCode.PLUGIN


    def read_range(self,
                   uuid: str,
                   local_series_folder: str,
                   content_type: orthanc.ContentType,
                   range_start: int,
                   size: int) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:

        logger.debug("read_range called",
                     uuid=uuid,
                     local_series_folder=local_series_folder,
                     content_type=str(content_type),
                     range_start=range_start,
                     size=size)

        try:
            data: bytes = self._read_file(uuid=uuid,
                                          local_series_folder=local_series_folder,
                                          content_type=content_type,
                                          range_start=range_start,
                                          size=size)

            logger.debug("read_range succeeded",
                         uuid=uuid,
                         bytes_read=len(data))
            return orthanc.ErrorCode.SUCCESS, data
        except FileNotFoundError:
            logger.error("file not found in local storage",
                         uuid=uuid,
                         local_series_folder=local_series_folder,
                         content_type=str(content_type))
            return orthanc.ErrorCode.UNKNOWN_RESOURCE, None
        except Exception as e:
            logger.error("error reading file from local storage",
                         uuid=uuid,
                         local_series_folder=local_series_folder,
                         error=str(e))
            return orthanc.ErrorCode.PLUGIN, None


    def remove(self,
               uuid: str,
               local_series_folder: str,
               content_type: orthanc.ContentType,
               file_size: int) -> None:

        # Note: if it appears that deletions are too slow, we should implement an asynchronous file deleter.

        with self.lease_folder(local_series_folder=local_series_folder):
            path: str = self.get_local_path(uuid=uuid,
                                            local_series_folder=local_series_folder,
                                            content_type=content_type)

            # os.path.exists() + os.remove() is not atomic: eviction can rmtree
            # the parent folder between the two calls. Catch FileNotFoundError
            # rather than letting it surface as a storage callback error.
            try:
                os.remove(path)
                existed: bool = True
                self._rollback_write_reservation(file_size)
            except FileNotFoundError:
                existed = False

            logger.debug("remove called",
                        uuid=uuid,
                        path=path,
                        existed=existed)


    def get_local_path(self, uuid: str, local_series_folder: str, content_type: orthanc.ContentType) -> str:

        if content_type not in self.SUPPORTED_CONTENT_TYPES:
            raise RuntimeError(f"Unsupported content type: {content_type}")

        return os.path.join(self._root, os.path.join(local_series_folder, uuid))

    def get_folder_path(self, local_series_folder: str) -> str:
        """Returns the full path for a series folder."""
        return os.path.join(self._root, local_series_folder)

    def has_local_file(self, uuid: str, local_series_folder: str, content_type: orthanc.ContentType) -> bool:
        path: str = self.get_local_path(uuid=uuid,
                                        local_series_folder=local_series_folder,
                                        content_type=content_type)
        exists: bool = os.path.exists(path)

        logger.debug("has_local_file check",
                     uuid=uuid,
                     local_series_folder=local_series_folder,
                     path=path,
                     exists=exists)
        return exists
