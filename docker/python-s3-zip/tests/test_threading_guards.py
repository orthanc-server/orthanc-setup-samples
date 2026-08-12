import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


PLUGIN_DIR = Path(__file__).resolve().parents[1] / "plugin"
sys.path.insert(0, str(PLUGIN_DIR))


class _ContentType:
    DICOM = 1
    DICOM_UNTIL_PIXEL_DATA = 3


class _ErrorCode:
    SUCCESS = "SUCCESS"
    UNKNOWN_RESOURCE = "UNKNOWN_RESOURCE"
    PLUGIN = "PLUGIN"


class _CompressionType:
    NONE = 0


class _DicomInstance:
    pass


class _QueueOrigin:
    FRONT = "front"
    BACK = "back"


class _OrthancException(Exception):
    """Stand-in for orthanc.OrthancException in unit tests."""
    pass


def _unimplemented(*_args, **_kwargs):
    # Default for any orthanc.* method the test doesn't explicitly stub.
    # If a code path under test hits one of these, the test should patch
    # it explicitly rather than silently calling a no-op.
    raise NotImplementedError("orthanc API not stubbed for this test")


# orthanc stub to emulate the various APIs required by the plugin
orthanc_stub = types.SimpleNamespace(
    ContentType=_ContentType,
    ErrorCode=_ErrorCode,
    CompressionType=_CompressionType,
    DicomInstance=_DicomInstance,
    OrthancException=_OrthancException,
    QueueOrigin=_QueueOrigin,
    LogInfo=lambda message: None,
    SetCurrentThreadName=lambda name: None,
    SetAttachmentCustomData=lambda uuid, custom_data: None,
    # These are filled in per-test via mock.patch.object as needed.
    ReserveQueueValue=_unimplemented,
    EnqueueValue=_unimplemented,
    AcknowledgeQueueValue=_unimplemented,
    RestApiGet=_unimplemented,
    RestApiPost=_unimplemented,
    RestApiDelete=_unimplemented,
    StoreKeyValue=_unimplemented,
    DeleteKeyValue=_unimplemented,
    CreateKeysValuesIterator=_unimplemented,
    GetAttachmentCustomData=_unimplemented,
    GetKeyValue=_unimplemented,
)
sys.modules.setdefault("orthanc", orthanc_stub)
sys.modules.setdefault("boto3", types.SimpleNamespace(client=object))


from custom_data import CustomData
from helpers import Helpers
from local_storage import _FUTILE_EVICTION_COOLDOWN_SEC, LocalStorage
from local_to_s3_zip_manager import (
    _COPY_QUEUE_IDLE_SLEEP_SECONDS,
    _COPY_QUEUE_MAX_DEFERRALS_BEFORE_IDLE,
    LOST_DATA_KVS,
    LocalToS3ZipManager,
)
from s3_zip_storage import (
    DELETED_SERIES_KVS,
    _HOUSEKEEPER_MAX_INSTANCES_PROBED_PER_SERIES,
    _HOUSEKEEPER_MAX_SERIES_PER_PASS,
    S3ZipStorage,
)
from uncommitted_series_handler import UNCOMMITTED_SERIES_KVS


def _fake_du_for(root: str, folder_name: str = "series", folder_size: int = 10):
    """Returns a fake subprocess.run side effect that simulates `du` output for a single folder under `root`."""
    # NOTE: **kwargs, not a fixed signature. LocalStorage._run_du_capture has
    # already changed the keywords it passes once (it dropped check=True when
    # it started tolerating a non-zero exit with usable output), which silently
    # broke every test in this file that builds a LocalStorage.
    def fake_run(cmd, capture_output=True, text=True, **_kwargs):
        folder = os.path.join(root, folder_name)
        total_size = folder_size if os.path.isdir(folder) else 0
        lines = []
        if os.path.isdir(folder):
            lines.append(f"{folder_size}\t{folder}")
        lines.append(f"{total_size}\t{root}")
        return subprocess.CompletedProcess(cmd, 0, stdout="\n".join(lines), stderr="")

    return fake_run


def _fake_du_walk(root: str):
    """Generic du substitute: walks ``root`` and sums real file sizes per child."""
    def fake_run(cmd, capture_output=True, text=True, **_kwargs):
        lines = []
        total = 0
        if os.path.isdir(root):
            for entry in os.listdir(root):
                child = os.path.join(root, entry)
                if not os.path.isdir(child):
                    continue
                size = 0
                for dirpath, _dirnames, filenames in os.walk(child):
                    for fname in filenames:
                        try:
                            size += os.path.getsize(os.path.join(dirpath, fname))
                        except OSError:
                            pass
                lines.append(f"{size}\t{child}")
                total += size
        lines.append(f"{total}\t{root}")
        return subprocess.CompletedProcess(cmd, 0, stdout="\n".join(lines), stderr="")
    return fake_run


class FolderLeaseTests(unittest.TestCase):
    def test_leased_folder_is_skipped_by_eviction_then_evicted_after_release(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, "series")
            os.makedirs(folder)
            with open(os.path.join(folder, "instance"), "wb") as f:
                f.write(b"abc")
            with open(os.path.join(folder, ".s3-uploaded"), "w") as f:
                f.write("series.zip")

            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage = LocalStorage(root=root, max_size_mb=1)
                storage.set_eviction_guard(lambda folder_name: True)

                with storage.lease_folder("series"):
                    result = storage.evict_all_safe()
                    self.assertEqual(result.freed_folders, 0)
                    self.assertEqual(result.skipped_folders, 1)
                    self.assertTrue(os.path.isdir(folder))

                result = storage.evict_all_safe()
                self.assertEqual(result.freed_folders, 1)
                self.assertFalse(os.path.exists(folder))

    def test_make_room_rolls_back_reservation_when_slow_path_fails(self):
        with tempfile.TemporaryDirectory() as root:
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage = LocalStorage(root=root, max_size_mb=0)

            storage._available_size = 0
            storage._reserved_bytes = 0

            with mock.patch.object(
                storage,
                "_update_local_storage_stats_with_writes_paused",
                side_effect=RuntimeError("scan failed"),
            ):
                with self.assertRaises(RuntimeError):
                    storage._make_room(10)

            self.assertEqual(storage._reserved_bytes, 0)
            self.assertEqual(storage._available_size, 0)
            self.assertFalse(storage._scan_in_progress)

    def test_eviction_keeps_folder_queued_when_delete_fails(self):
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, "series")
            os.makedirs(folder)
            with open(os.path.join(folder, "instance"), "wb") as f:
                f.write(b"abc")

            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage = LocalStorage(root=root, max_size_mb=1)
                storage.set_eviction_guard(lambda folder_name: True)

                with mock.patch("local_storage.shutil.rmtree", side_effect=OSError("locked")):
                    result = storage.evict_all_safe()

            self.assertEqual(result.freed_folders, 0)
            self.assertEqual(result.skipped_folders, 1)
            self.assertTrue(os.path.isdir(folder))

    def test_pause_writes_for_scan_clears_flag_when_wait_is_interrupted(self):
        # Regression: if `wait()` raises after `_scan_in_progress` is set, the
        # flag must be cleared and waiters notified. Otherwise every future
        # write/scan deadlocks at `_enter_write` / `_pause_writes_for_scan`.
        with tempfile.TemporaryDirectory() as root:
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage = LocalStorage(root=root, max_size_mb=1)

            # Make sure the active-writers wait loop is taken.
            storage._active_writers = 1

            with mock.patch.object(
                storage._io_condition,
                "wait",
                side_effect=KeyboardInterrupt("simulated signal"),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    storage._pause_writes_for_scan()

            self.assertFalse(storage._scan_in_progress)

            # And a fresh scan can still acquire the slot afterwards.
            storage._active_writers = 0
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage._update_local_storage_stats()
            self.assertFalse(storage._scan_in_progress)

    def test_folder_marker_critical_section_serializes_same_folder(self):
        # Two threads asking for the SAME folder's CS must serialize. Two
        # threads asking for DIFFERENT folders must run in parallel.
        with tempfile.TemporaryDirectory() as root:
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage = LocalStorage(root=root, max_size_mb=1)

            inside_same = threading.Event()
            release_same = threading.Event()
            second_acquired_same = threading.Event()

            def first_same():
                with storage.folder_marker_critical_section("series"):
                    inside_same.set()
                    self.assertTrue(release_same.wait(timeout=2))

            def second_same():
                self.assertTrue(inside_same.wait(timeout=2))
                # Should block until release_same fires.
                with storage.folder_marker_critical_section("series"):
                    second_acquired_same.set()

            t1 = threading.Thread(target=first_same)
            t2 = threading.Thread(target=second_same)
            t1.start(); t2.start()
            self.assertTrue(inside_same.wait(timeout=2))
            self.assertFalse(
                second_acquired_same.wait(timeout=0.1),
                "second caller for same folder must wait while first holds the section",
            )
            release_same.set()
            t1.join(timeout=2); t2.join(timeout=2)
            self.assertTrue(second_acquired_same.is_set())
            self.assertEqual(storage._folder_marker_cs_locks, {})

            # Different folder: must NOT block.
            inside_a = threading.Event()
            release_a = threading.Event()
            inside_b = threading.Event()

            def folder_a():
                with storage.folder_marker_critical_section("a"):
                    inside_a.set()
                    self.assertTrue(release_a.wait(timeout=2))

            def folder_b():
                self.assertTrue(inside_a.wait(timeout=2))
                with storage.folder_marker_critical_section("b"):
                    inside_b.set()

            ta = threading.Thread(target=folder_a)
            tb = threading.Thread(target=folder_b)
            ta.start(); tb.start()
            self.assertTrue(
                inside_b.wait(timeout=2),
                "different-folder caller must not be blocked by holder of another folder",
            )
            release_a.set()
            ta.join(timeout=2); tb.join(timeout=2)
            self.assertEqual(storage._folder_marker_cs_locks, {})

    def test_marker_critical_section_prevents_stale_marker_in_race_window(self):
        # The classic interleaving the mutex is here to forbid:
        #   copy:   takes CS, runs recheck (snapshot match) -> writes marker
        #   create: takes CS afterwards, deletes marker
        # End state must be NO marker. Without the mutex, create's invalidate
        # could land between copy's recheck and copy's marker write, leaving
        # a stale marker that hides an un-uploaded file.
        with tempfile.TemporaryDirectory() as root:
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage = LocalStorage(root=root, max_size_mb=1)

            folder = os.path.join(root, "series")
            os.makedirs(folder)
            marker_path = os.path.join(folder, ".s3-uploaded")

            copy_inside_cs = threading.Event()
            copy_finished_recheck = threading.Event()
            create_done = threading.Event()

            def copy_side():
                with storage.folder_marker_critical_section("series"):
                    copy_inside_cs.set()
                    # Let create_side try (and block) before we publish.
                    time.sleep(0.05)
                    copy_finished_recheck.set()
                    with open(marker_path, "w") as f:
                        _ = f.write("series.zip")

            def create_side():
                self.assertTrue(copy_inside_cs.wait(timeout=2))
                # This must block on the mutex until copy_side releases.
                with storage.folder_marker_critical_section("series"):
                    self.assertTrue(
                        copy_finished_recheck.is_set(),
                        "create entered CS before copy finished its recheck-and-publish window",
                    )
                    try:
                        os.remove(marker_path)
                    except FileNotFoundError:
                        pass
                    create_done.set()

            t_copy = threading.Thread(target=copy_side)
            t_create = threading.Thread(target=create_side)
            t_copy.start(); t_create.start()
            t_copy.join(timeout=2); t_create.join(timeout=2)

            self.assertTrue(create_done.is_set())
            self.assertFalse(
                os.path.exists(marker_path),
                "create's invalidate must win the end state; mutex orders the two",
            )
            self.assertEqual(storage._folder_marker_cs_locks, {})

    def test_remove_swallows_filenotfound_race_with_eviction(self):
        # Eviction can rmtree the parent folder between `os.path.exists` and
        # `os.remove`. The remove path must absorb that race instead of letting
        # FileNotFoundError leak back to Orthanc's storage callback.
        with tempfile.TemporaryDirectory() as root:
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_for(root)):
                storage = LocalStorage(root=root, max_size_mb=1)

            with mock.patch("local_storage.os.remove", side_effect=FileNotFoundError("gone")):
                # Must not raise.
                storage.remove(
                    uuid="instance",
                    local_series_folder="series",
                    content_type=orthanc_stub.ContentType.DICOM,
                    file_size=0
                )


class SpacePressureTests(unittest.TestCase):
    """Behaviour when the cache is full -- a designed-for state, not an edge case.

    The local cache is deliberately allowed to exceed its configured ceiling:
    every folder still waiting for its S3 upload is protected from eviction,
    so a burst of ingest legitimately has nothing to free. What must not
    happen is the server making that situation worse.
    """

    def _storage(self, root, max_size_mb=1):
        with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
            return LocalStorage(root=root, max_size_mb=max_size_mb)

    def test_partially_written_file_is_removed_when_the_write_fails(self):
        # ENOSPC mid-write leaves a truncated file. Orthanc fails the C-STORE
        # and never references it, but the bytes stay: they occupy the cache
        # and, since no zip can ever account for them, they would keep the
        # folder ineligible for eviction for the life of the pod.
        with tempfile.TemporaryDirectory() as root:
            storage = self._storage(root)

            real_open = open

            def failing_open(path, *args, **kwargs):
                handle = real_open(path, *args, **kwargs)
                if os.path.basename(path) == "instance":
                    handle.close()
                    raise OSError(28, "No space left on device")
                return handle

            # The du mock stays on: write_file refreshes the stats after a
            # failed write, and `du -b` is GNU-only (it does not exist on the
            # macOS where developers run this suite).
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                with mock.patch("builtins.open", side_effect=failing_open):
                    with self.assertRaises(OSError):
                        storage.write_file(local_series_folder="series",
                                           uuid="instance",
                                           content=b"payload")

            self.assertFalse(
                os.path.exists(os.path.join(root, "series", "instance")),
                "a truncated file must not survive the write that failed",
            )

    def test_failed_write_is_reported_to_orthanc_rather_than_silently_swallowed(self):
        # The C-STORE must fail so the modality retries; returning SUCCESS
        # would leave Orthanc's index pointing at bytes that do not exist.
        with tempfile.TemporaryDirectory() as root:
            storage = self._storage(root)

            with mock.patch.object(storage, "write_file",
                                   side_effect=OSError(28, "No space left on device")):
                error_code = storage.create(
                    uuid="instance",
                    local_series_folder="series",
                    content_type=orthanc_stub.ContentType.DICOM,
                    compression_type=orthanc_stub.CompressionType.NONE,
                    content=b"payload",
                )

            self.assertEqual(error_code, orthanc_stub.ErrorCode.PLUGIN)

    def test_a_futile_eviction_pass_stops_the_rescan_storm(self):
        # Once over budget with everything protected, every single instance
        # write used to pause all writers, fork a du over the whole cache and
        # walk the LRU queue -- to free nothing, then write anyway. The cost
        # of ingesting one instance became proportional to the size of the
        # cache, exactly when the server could least afford it.
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, "series")
            os.makedirs(folder)
            with open(os.path.join(folder, "instance"), "wb") as f:
                _ = f.write(b"x" * 4096)

            storage = self._storage(root, max_size_mb=0)
            # Nothing here is on S3, so nothing is evictable.
            storage.set_eviction_guard(lambda folder_name: False)

            scans = []
            real_scan = storage._update_local_storage_stats_with_writes_paused

            def counting_scan():
                scans.append(1)
                return real_scan()

            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                with mock.patch.object(storage, "_update_local_storage_stats_with_writes_paused",
                                       side_effect=counting_scan):
                    for _ in range(10):
                        storage._commit_write_reservation(storage._make_room(1000))

            self.assertEqual(len(scans), 1,
                             "a futile eviction pass must not be repeated on every write")

            # ... and the pause is time-bounded, not permanent: once it
            # expires the next write scans again and the accounting
            # self-corrects.
            storage._futile_eviction_until = time.monotonic() - 0.01
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                with mock.patch.object(storage, "_update_local_storage_stats_with_writes_paused",
                                       side_effect=counting_scan):
                    storage._commit_write_reservation(storage._make_room(1000))
            self.assertEqual(len(scans), 2)
            self.assertGreater(_FUTILE_EVICTION_COOLDOWN_SEC, 0)

    def test_freeing_space_re_enables_the_rescan(self):
        # The cooldown is about "nothing to free", so anything that frees
        # something must cancel it immediately rather than let writes coast on
        # stale accounting.
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, "series")
            os.makedirs(folder)
            with open(os.path.join(folder, "instance"), "wb") as f:
                _ = f.write(b"x" * 4096)
            with open(os.path.join(folder, ".s3-uploaded"), "w") as f:
                _ = f.write("series.zip")

            storage = self._storage(root)
            storage.set_eviction_guard(lambda folder_name: True)
            storage._futile_eviction_until = time.monotonic() + 3600

            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                result = storage.evict_all_safe()

            self.assertEqual(result.freed_folders, 1)
            self.assertEqual(storage._futile_eviction_until, 0.0)

    def test_removing_the_last_instance_drops_the_empty_folder(self):
        # An empty folder is not free: du charges it a block, so the cache
        # never reports zero usage again, and with no marker it counts as
        # "not yet on S3" in every stats snapshot and eviction pass.
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, "series")
            os.makedirs(folder)
            for name in ("instance-1", "instance-2"):
                with open(os.path.join(folder, name), "wb") as f:
                    _ = f.write(b"x")
            with open(os.path.join(folder, ".s3-uploaded"), "w") as f:
                _ = f.write("series.zip")

            storage = self._storage(root)

            storage.remove(uuid="instance-1",
                           local_series_folder="series",
                           content_type=orthanc_stub.ContentType.DICOM,
                           file_size=1)
            self.assertTrue(os.path.isdir(folder), "the folder still holds an instance")

            storage.remove(uuid="instance-2",
                           local_series_folder="series",
                           content_type=orthanc_stub.ContentType.DICOM,
                           file_size=1)
            self.assertFalse(os.path.exists(folder),
                             "the last instance's removal must take the husk with it")

    def test_write_recreates_a_folder_that_vanished_under_it(self):
        # The empty-folder cleanup and eviction both race storage_create. A
        # folder disappearing between makedirs and open must cost one retry,
        # not a failed C-STORE.
        with tempfile.TemporaryDirectory() as root:
            storage = self._storage(root)

            folder = os.path.join(root, "series")
            real_open = open
            opens = []

            def racing_open(path, *args, **kwargs):
                if os.path.basename(path) == "instance" and not opens:
                    opens.append(path)
                    shutil.rmtree(folder, ignore_errors=True)
                    raise FileNotFoundError(path)
                return real_open(path, *args, **kwargs)

            with mock.patch("builtins.open", side_effect=racing_open):
                storage.write_file(local_series_folder="series",
                                   uuid="instance",
                                   content=b"payload")

            with open(os.path.join(folder, "instance"), "rb") as f:
                self.assertEqual(f.read(), b"payload")

    def test_deleting_a_file_does_not_cancel_another_writer_s_reservation(self):
        # Reserved bytes belong to writes that are still in flight. Crediting
        # a deletion against them makes the cache look emptier than it is,
        # which is the wrong direction to be wrong in.
        with tempfile.TemporaryDirectory() as root:
            storage = self._storage(root)

            storage._reserved_bytes = 5000
            available_before = storage._available_size

            with mock.patch("local_storage.os.remove"):
                storage.remove(uuid="instance",
                               local_series_folder="series",
                               content_type=orthanc_stub.ContentType.DICOM,
                               file_size=1000)

            self.assertEqual(storage._reserved_bytes, 5000)
            self.assertEqual(storage._available_size, available_before + 1000)


class ConcurrentStressTests(unittest.TestCase):
    """Best-effort multi-thread stress.

    Spins up a real ``LocalStorage`` against a real temp directory and runs
    writers, readers, removers and evictors against it concurrently. Each
    worker uses the public storage API just like Orthanc would. The asserts
    only check global invariants -- no exceptions surface, accounting
    stays consistent, and no scan slot or write count is left dangling.
    """

    def test_writers_readers_evictor_keep_state_consistent(self):
        import random

        with tempfile.TemporaryDirectory() as root:
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                # Generous budget so the fast path is usually taken, but small
                # enough that some calls cross the slow path during the run.
                storage = LocalStorage(root=root, max_size_mb=4)

                # Treat every folder as safe to evict so eviction actually fires.
                storage.set_eviction_guard(lambda folder_name: True)

                folders = [f"series-{i}" for i in range(6)]
                stop = threading.Event()
                errors: list[BaseException] = []
                errors_lock = threading.Lock()

                def record(exc: BaseException) -> None:
                    with errors_lock:
                        errors.append(exc)

                def writer(seed: int) -> None:
                    rng = random.Random(seed)
                    with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                        for _ in range(60):
                            if stop.is_set():
                                return
                            folder = rng.choice(folders)
                            uuid = f"u-{rng.randint(0, 999)}-{seed}-{_}"
                            content = os.urandom(rng.randint(64, 4096))
                            try:
                                storage.write_file(local_series_folder=folder, uuid=uuid, content=content)
                            except Exception as e:
                                record(e)
                                return

                def reader(seed: int) -> None:
                    rng = random.Random(seed + 1000)
                    for _ in range(80):
                        if stop.is_set():
                            return
                        folder = rng.choice(folders)
                        uuid = f"u-{rng.randint(0, 999)}-{seed}-{_}"
                        try:
                            with storage.lease_folder(folder):
                                if storage.has_local_file(
                                    uuid=uuid,
                                    local_series_folder=folder,
                                    content_type=orthanc_stub.ContentType.DICOM,
                                ):
                                    storage.read_file(uuid=uuid, local_series_folder=folder)
                        except FileNotFoundError:
                            # Acceptable: file was evicted/removed between
                            # has_local_file and read; the lease only protects
                            # the folder, not individual files post-eviction.
                            pass
                        except Exception as e:
                            record(e)
                            return

                def remover(seed: int) -> None:
                    rng = random.Random(seed + 2000)
                    for _ in range(40):
                        if stop.is_set():
                            return
                        folder = rng.choice(folders)
                        uuid = f"u-{rng.randint(0, 999)}-{seed}-{_}"
                        try:
                            storage.remove(
                                uuid=uuid,
                                local_series_folder=folder,
                                content_type=orthanc_stub.ContentType.DICOM,
                                file_size=0
                            )
                        except Exception as e:
                            record(e)
                            return

                def evictor() -> None:
                    with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                        for _ in range(15):
                            if stop.is_set():
                                return
                            try:
                                storage.evict_all_safe()
                            except Exception as e:
                                record(e)
                                return

                threads: list[threading.Thread] = []
                for i in range(4):
                    threads.append(threading.Thread(target=writer, args=(i,)))
                for i in range(4):
                    threads.append(threading.Thread(target=reader, args=(i,)))
                for i in range(2):
                    threads.append(threading.Thread(target=remover, args=(i,)))
                threads.append(threading.Thread(target=evictor))

                for t in threads:
                    t.start()

                deadline = time.monotonic() + 8
                for t in threads:
                    remaining = max(0.1, deadline - time.monotonic())
                    t.join(timeout=remaining)
                stop.set()

                for t in threads:
                    if t.is_alive():
                        self.fail(f"thread did not finish in time: {t.name}")

                if errors:
                    self.fail(f"workers raised: {[type(e).__name__ + ': ' + str(e) for e in errors]}")

                # Drain any final state with one more refresh so accounting
                # reflects what is actually on disk.
                with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                    storage._update_local_storage_stats()

                # Global invariants after the storm.
                self.assertEqual(storage._active_writers, 0)
                self.assertFalse(storage._scan_in_progress)
                self.assertEqual(storage._folder_lease_counts, {})
                self.assertEqual(storage._reserved_bytes, 0)
                # Available + apparent disk usage must equal max_size after
                # a fresh rescan (no reservations leaked).
                used_estimate = storage._max_size - storage._available_size
                self.assertGreaterEqual(used_estimate, 0)
                self.assertLessEqual(used_estimate, storage._max_size)


class _ReadPathLocalStorage:
    def __init__(self):
        self.lease_depth = 0
        self.read_saw_lease = False

    @contextmanager
    def lease_folder(self, local_series_folder):
        self.lease_depth += 1
        try:
            yield
        finally:
            self.lease_depth -= 1

    def has_local_file(self, uuid, local_series_folder, content_type):
        if self.lease_depth <= 0:
            raise AssertionError("has_local_file called without a folder lease")
        return True

    def read_range(self, uuid, local_series_folder, content_type, range_start, size):
        if self.lease_depth <= 0:
            raise AssertionError("read_range called without a folder lease")
        self.read_saw_lease = True
        return orthanc_stub.ErrorCode.SUCCESS, b"dicom"


class _UnusedZipManager:
    def retrieve_zip_from_s3(self, s3_zip_key, local_series_folder):
        raise AssertionError("retrieve_zip_from_s3 should not be called for a local hit")


class S3ZipStorageReadTests(unittest.TestCase):
    def test_local_hit_keeps_folder_leased_from_check_through_read(self):
        local_storage = _ReadPathLocalStorage()
        storage = S3ZipStorage.__new__(S3ZipStorage)
        storage._local_storage = local_storage
        storage._zip_manager = _UnusedZipManager()

        custom_data = CustomData(
            storage=CustomData.Storage.S3_ZIP,
            local_series_folder="series",
            s3_zip_key="series.zip",
            # Required since CustomData.from_json started rejecting S3_ZIP
            # payloads without one; without it this whole test was silently
            # exercising the "broken custom data" branch instead of the
            # local-hit path it is named after.
            series_id="series-of-instance",
            size_in_bytes=0
        ).to_binary()

        error_code, data = storage.storage_read_range(
            uuid="instance",
            content_type=orthanc_stub.ContentType.DICOM,
            range_start=0,
            size=0,
            custom_data=custom_data,
        )

        self.assertEqual(error_code, orthanc_stub.ErrorCode.SUCCESS)
        self.assertEqual(data, b"dicom")
        self.assertTrue(local_storage.read_saw_lease)
        self.assertEqual(local_storage.lease_depth, 0)


class _CreatePathLocalStorage:
    """Records what was leased while storage_create did its work."""

    def __init__(self):
        self.lease_depth = 0
        self.leased_folders = []
        self.create_saw_lease = None
        self.marker_cs_saw_lease = None

    @contextmanager
    def lease_folder(self, local_series_folder):
        self.lease_depth += 1
        self.leased_folders.append(local_series_folder)
        try:
            yield
        finally:
            self.lease_depth -= 1

    @contextmanager
    def folder_marker_critical_section(self, local_series_folder):
        self.marker_cs_saw_lease = self.lease_depth > 0
        yield

    def create(self, uuid, local_series_folder, content_type, compression_type, content):
        self.create_saw_lease = self.lease_depth > 0
        return orthanc_stub.ErrorCode.SUCCESS


class _InvalidatingZipManager:
    def __init__(self, local_storage):
        self._local_storage = local_storage
        self.invalidate_saw_lease = None

    def invalidate_s3_uploaded_marker(self, local_series_folder):
        self.invalidate_saw_lease = self._local_storage.lease_depth > 0
        return True


class _FakeDicomInstance:
    def GetInstanceSimplifiedJson(self):
        return json.dumps({
            "PatientID": "PAT",
            "StudyInstanceUID": "1.2.3",
            "SeriesInstanceUID": "1.2.3.4",
        })


class S3ZipStorageCreateTests(unittest.TestCase):
    def test_create_and_marker_invalidation_run_under_one_folder_lease(self):
        # A folder already on S3 carries a marker, and that marker is
        # eviction's permission to delete it. The instance being written is
        # NOT in that S3 zip, so between "file written" and "marker removed"
        # the folder is a legal eviction target holding data that exists
        # nowhere else. The window is small; an eviction pass running every
        # couple of seconds against a busy ingest finds it. The lease is what
        # makes eviction skip the folder for the whole window.
        local_storage = _CreatePathLocalStorage()
        zip_manager = _InvalidatingZipManager(local_storage)

        storage = S3ZipStorage.__new__(S3ZipStorage)
        storage._local_storage = local_storage
        storage._zip_manager = zip_manager

        error_code, custom_data = storage.storage_create(
            uuid="instance",
            content_type=orthanc_stub.ContentType.DICOM,
            compression_type=orthanc_stub.CompressionType.NONE,
            content=b"payload",
            dicom_instance=_FakeDicomInstance(),
        )

        self.assertEqual(error_code, orthanc_stub.ErrorCode.SUCCESS)
        self.assertTrue(local_storage.create_saw_lease, "the write must hold the folder lease")
        self.assertTrue(local_storage.marker_cs_saw_lease)
        self.assertTrue(zip_manager.invalidate_saw_lease,
                        "the marker invalidation must still hold the lease taken for the write")
        self.assertEqual(local_storage.lease_depth, 0, "the lease must be released")

        cd = CustomData.from_binary(custom_data)
        self.assertEqual(cd.storage, CustomData.Storage.LOCAL)
        self.assertEqual(local_storage.leased_folders, [cd.local_series_folder])


class _BlockingInvalidateZipManager:
    """Holds storage_create inside the marker-invalidation step on demand."""

    def __init__(self, root, folder_name, entered, may_proceed):
        self.marker_path = os.path.join(root, folder_name, ".s3-uploaded")
        self.entered = entered
        self.may_proceed = may_proceed

    def invalidate_s3_uploaded_marker(self, local_series_folder):
        self.entered.set()
        self.may_proceed.wait(timeout=5)
        try:
            os.remove(self.marker_path)
            return True
        except FileNotFoundError:
            return False


class StorageCreateVersusEvictionTests(unittest.TestCase):
    """The exact interleaving that destroyed a DICOM instance in CI.

    Real LocalStorage, real eviction, real marker file. A folder that is
    already on S3 receives a new instance; the eviction pass fires in the
    window between the file landing on disk and the marker being invalidated.
    """

    def test_eviction_skips_a_folder_that_is_taking_a_new_instance(self):
        with tempfile.TemporaryDirectory() as root:
            dicom_instance = _FakeDicomInstance()
            folder_name = Helpers.get_series_hash(dicom_instance)
            folder = os.path.join(root, folder_name)
            os.makedirs(folder)

            # The state that makes this dangerous: everything currently in the
            # folder is in the S3 zip, so the marker says "safe to evict".
            with open(os.path.join(folder, "already-uploaded"), "wb") as f:
                _ = f.write(b"old")
            with open(os.path.join(folder, ".s3-uploaded"), "w") as f:
                _ = f.write("series.zip")

            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                local_storage = LocalStorage(root=root, max_size_mb=1)
            local_storage.set_eviction_guard(
                lambda name: os.path.exists(os.path.join(root, name, ".s3-uploaded"))
            )

            entered_invalidate = threading.Event()
            may_finish_invalidate = threading.Event()

            storage = S3ZipStorage.__new__(S3ZipStorage)
            storage._local_storage = local_storage
            storage._zip_manager = _BlockingInvalidateZipManager(
                root, folder_name, entered_invalidate, may_finish_invalidate
            )

            eviction_result = {}

            def create_side():
                storage.storage_create(
                    uuid="brand-new-instance",
                    content_type=orthanc_stub.ContentType.DICOM,
                    compression_type=orthanc_stub.CompressionType.NONE,
                    content=b"the bytes that used to get deleted",
                    dicom_instance=dicom_instance,
                )

            def evict_side():
                self.assertTrue(entered_invalidate.wait(timeout=5))
                with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                    eviction_result["result"] = local_storage.evict_all_safe()
                may_finish_invalidate.set()

            t_create = threading.Thread(target=create_side)
            t_evict = threading.Thread(target=evict_side)
            t_create.start(); t_evict.start()
            t_create.join(timeout=10); t_evict.join(timeout=10)

            self.assertFalse(t_create.is_alive())
            self.assertFalse(t_evict.is_alive())

            # The marker was still on disk when eviction ran, so the guard
            # said "safe". Only the folder lease taken by storage_create keeps
            # the pass off it.
            self.assertEqual(eviction_result["result"].freed_folders, 0)
            self.assertEqual(eviction_result["result"].skipped_folders, 1)
            with open(os.path.join(folder, "brand-new-instance"), "rb") as f:
                self.assertEqual(f.read(), b"the bytes that used to get deleted")

            # And once the invalidation completes, the folder is correctly
            # protected by the absence of the marker instead.
            self.assertFalse(os.path.exists(os.path.join(folder, ".s3-uploaded")))
            with mock.patch("local_storage.subprocess.run", side_effect=_fake_du_walk(root)):
                after = local_storage.evict_all_safe()
            self.assertEqual(after.freed_folders, 0)
            self.assertTrue(os.path.exists(os.path.join(folder, "brand-new-instance")))


class _RetrievalLocalStorage:
    def __init__(self, root=None):
        self.root = root
        self.lease_depth = 0
        self.max_lease_depth = 0
        self.marker_cs_depth = 0
        self.max_marker_cs_depth = 0
        self.writes = []
        # Optional hook fired right before the marker critical section is
        # entered, used by tests to simulate a concurrent storage_create
        # landing a new instance in the folder during retrieval.
        self.before_marker_cs = None

    @contextmanager
    def lease_folder(self, local_series_folder):
        self.lease_depth += 1
        self.max_lease_depth = max(self.max_lease_depth, self.lease_depth)
        try:
            yield
        finally:
            self.lease_depth -= 1

    @contextmanager
    def folder_marker_critical_section(self, local_series_folder):
        if self.before_marker_cs is not None:
            self.before_marker_cs(local_series_folder)
        self.marker_cs_depth += 1
        self.max_marker_cs_depth = max(self.max_marker_cs_depth, self.marker_cs_depth)
        try:
            yield
        finally:
            self.marker_cs_depth -= 1

    def get_folder_path(self, local_series_folder):
        if self.root is None:
            raise AssertionError("get_folder_path requires a root tempdir")
        return os.path.join(self.root, local_series_folder)

    def write_file(self, local_series_folder, uuid, content):
        if self.lease_depth <= 0:
            raise AssertionError("write_file called without a folder lease")
        self.writes.append((local_series_folder, uuid, content))
        if self.root is not None:
            folder = os.path.join(self.root, local_series_folder)
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, uuid), "wb") as f:
                f.write(content)

    def read_file(self, local_series_folder, uuid):
        raise AssertionError("read_file is not used by retrieval")


class _ZipS3Client:
    def download_file(self, bucket_name, s3_zip_key, destination_path):
        with zipfile.ZipFile(destination_path, "w") as zipf:
            zipf.writestr("a", b"A")
            zipf.writestr("b", b"B")


class _FlakyZipS3Client:
    def __init__(self, failures_before_success):
        self.failures_before_success = failures_before_success
        self.download_attempts = 0

    def download_file(self, bucket_name, s3_zip_key, destination_path):
        self.download_attempts += 1
        if self.download_attempts <= self.failures_before_success:
            raise ConnectionError("temporary S3 connection glitch")
        with zipfile.ZipFile(destination_path, "w") as zipf:
            zipf.writestr("a", b"A")


class _BadZipS3Client:
    def __init__(self):
        self.download_attempts = 0

    def download_file(self, bucket_name, s3_zip_key, destination_path):
        self.download_attempts += 1
        with open(destination_path, "wb") as f:
            f.write(b"this is not a zip")


class _BlockingFailS3Client:
    def __init__(self):
        self.download_started = threading.Event()
        self.release_failure = threading.Event()
        self.download_attempts = 0

    def download_file(self, bucket_name, s3_zip_key, destination_path):
        self.download_attempts += 1
        self.download_started.set()
        self.release_failure.wait(timeout=5)
        raise ConnectionError("shared retrieval failure")


class ZipRetrievalTests(unittest.TestCase):
    def _new_manager(self, local_storage, s3_client=None, max_attempts=3):
        return LocalToS3ZipManager(
            s3_client=s3_client or _ZipS3Client(),
            bucket_name="bucket",
            local_storage=local_storage,
            enable_compression=False,
            uncommitted_series_handler=object(),
            s3_retrieval_max_attempts=max_attempts,
            s3_retrieval_retry_base_delay_sec=0,
            s3_retrieval_retry_max_delay_sec=0,
        )

    def test_retrieval_refcount_is_owned_by_manager_lock(self):
        manager = self._new_manager(_RetrievalLocalStorage())

        first, first_is_new = manager._acquire_zip_retrieval("series.zip")
        second, second_is_new = manager._acquire_zip_retrieval("series.zip")

        self.assertTrue(first_is_new)
        self.assertFalse(second_is_new)
        self.assertIs(first, second)
        self.assertEqual(first._ref_count, 2)

        manager._release_zip_retrieval(first)
        self.assertIs(manager._s3_zip_retrievals["series.zip"], first)
        self.assertEqual(first._ref_count, 1)

        manager._release_zip_retrieval(second)
        self.assertNotIn("series.zip", manager._s3_zip_retrievals)
        self.assertEqual(first._ref_count, 0)

    def test_retrieve_zip_from_s3_holds_folder_lease_while_extracting(self):
        with tempfile.TemporaryDirectory() as root:
            local_storage = _RetrievalLocalStorage(root=root)
            manager = self._new_manager(local_storage)

            manager.retrieve_zip_from_s3(
                s3_zip_key="series.zip",
                local_series_folder="series",
            )

            self.assertEqual(
                local_storage.writes,
                [("series", "a", b"A"), ("series", "b", b"B")],
            )
            self.assertGreaterEqual(local_storage.max_lease_depth, 1)
            self.assertEqual(local_storage.lease_depth, 0)
            self.assertEqual(manager._s3_zip_retrievals, {})
            # Marker is published on a clean retrieve so the folder is
            # immediately reported as "on S3" and is safe to evict.
            marker_path = os.path.join(root, "series", ".s3-uploaded")
            with open(marker_path, "r") as f:
                self.assertEqual(f.read(), "series.zip")
            self.assertGreaterEqual(local_storage.max_marker_cs_depth, 1)

    def test_retrieve_zip_from_s3_retries_transient_download_failure(self):
        with tempfile.TemporaryDirectory() as root:
            local_storage = _RetrievalLocalStorage(root=root)
            s3_client = _FlakyZipS3Client(failures_before_success=2)
            manager = self._new_manager(local_storage, s3_client=s3_client, max_attempts=3)

            manager.retrieve_zip_from_s3(
                s3_zip_key="series.zip",
                local_series_folder="series",
            )

            self.assertEqual(s3_client.download_attempts, 3)
            self.assertEqual(local_storage.writes, [("series", "a", b"A")])
            self.assertEqual(manager._s3_zip_retrievals, {})
            marker_path = os.path.join(root, "series", ".s3-uploaded")
            self.assertTrue(os.path.exists(marker_path))

    def test_retrieve_zip_from_s3_does_not_retry_bad_zip(self):
        local_storage = _RetrievalLocalStorage()
        s3_client = _BadZipS3Client()
        manager = self._new_manager(local_storage, s3_client=s3_client, max_attempts=3)

        with self.assertRaises(zipfile.BadZipFile):
            manager.retrieve_zip_from_s3(
                s3_zip_key="series.zip",
                local_series_folder="series",
            )

        self.assertEqual(s3_client.download_attempts, 1)
        self.assertEqual(local_storage.writes, [])
        self.assertEqual(manager._s3_zip_retrievals, {})
        # Failure path never reaches the marker block -- no get_folder_path
        # / CS calls are required from the mock when retrieval errors out.
        self.assertEqual(local_storage.max_marker_cs_depth, 0)

    def test_retrieve_zip_from_s3_writes_marker_only_when_folder_matches_zip(self):
        # Race protection: if a concurrent storage_create lands a new
        # instance in the same folder between extraction and the marker
        # write, the on-disk file set will not match the extracted set and
        # the marker must be withheld. Without this guard, eviction could
        # later purge the folder and lose that new instance.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _RetrievalLocalStorage(root=root)
            manager = self._new_manager(local_storage)

            def simulate_concurrent_storage_create(_folder):
                # storage_create writes its file BEFORE taking the marker
                # CS, so the extra file is on disk by the time the
                # retrieve thread enters the CS.
                with open(os.path.join(root, "series", "c"), "wb") as f:
                    f.write(b"new-instance-during-retrieve")

            local_storage.before_marker_cs = simulate_concurrent_storage_create

            manager.retrieve_zip_from_s3(
                s3_zip_key="series.zip",
                local_series_folder="series",
            )

            self.assertFalse(
                os.path.exists(os.path.join(root, "series", ".s3-uploaded")),
                "marker must not be written when folder has files outside the zip",
            )
            self.assertGreaterEqual(local_storage.max_marker_cs_depth, 1)
            # The two extracted files and the extra one all remain on disk;
            # the next STABLE_SERIES copy will pick them up and publish a
            # marker that reflects the new attachment set.
            self.assertTrue(os.path.exists(os.path.join(root, "series", "a")))
            self.assertTrue(os.path.exists(os.path.join(root, "series", "b")))
            self.assertTrue(os.path.exists(os.path.join(root, "series", "c")))

    def test_waiting_retrieval_callers_share_terminal_failure(self):
        local_storage = _RetrievalLocalStorage()
        s3_client = _BlockingFailS3Client()
        manager = self._new_manager(local_storage, s3_client=s3_client, max_attempts=1)
        errors = []

        def retrieve():
            try:
                manager.retrieve_zip_from_s3(
                    s3_zip_key="series.zip",
                    local_series_folder="series",
                )
            except Exception as e:
                errors.append(e)

        first = threading.Thread(target=retrieve)
        second = threading.Thread(target=retrieve)
        first.start()
        self.assertTrue(s3_client.download_started.wait(timeout=5))
        second.start()

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with manager._s3_zip_retrievals_lock:
                retrieval = manager._s3_zip_retrievals.get("series.zip")
                ref_count = retrieval._ref_count if retrieval is not None else 0
            if ref_count >= 2:
                break
            time.sleep(0.01)
        else:
            self.fail("second retrieval caller did not acquire the shared ZipRetrieval")

        s3_client.release_failure.set()
        first.join(timeout=5)
        second.join(timeout=5)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(len(errors), 2)
        self.assertTrue(all(isinstance(e, ConnectionError) for e in errors))
        self.assertEqual(s3_client.download_attempts, 1)
        self.assertEqual(manager._s3_zip_retrievals, {})


class _CopyLocalStorage:
    def __init__(self, root):
        self.root = root
        self.lease_depth = 0
        self.max_lease_depth = 0
        self.marker_cs_depth = 0
        self.max_marker_cs_depth = 0
        self.reads = []

    @contextmanager
    def lease_folder(self, local_series_folder):
        self.lease_depth += 1
        self.max_lease_depth = max(self.max_lease_depth, self.lease_depth)
        try:
            yield
        finally:
            self.lease_depth -= 1

    @contextmanager
    def folder_marker_critical_section(self, local_series_folder):
        self.marker_cs_depth += 1
        self.max_marker_cs_depth = max(self.max_marker_cs_depth, self.marker_cs_depth)
        try:
            yield
        finally:
            self.marker_cs_depth -= 1

    def read_file(self, uuid, local_series_folder):
        if self.lease_depth <= 0:
            raise AssertionError("read_file called without a folder lease")
        self.reads.append((uuid, local_series_folder))
        return f"content-{uuid}".encode("ascii")

    def write_file(self, local_series_folder, uuid, content):
        raise AssertionError("write_file is not used by copy_series_to_s3")

    def get_folder_path(self, local_series_folder):
        return os.path.join(self.root, local_series_folder)

    def has_local_file(self, uuid, local_series_folder, content_type):
        # Default: pretend everything is on disk. Individual tests
        # override via mock.patch.object when they want to exercise the
        # missing-file fast-path guard.
        return True


class _UploadS3Client:
    def __init__(self):
        self.uploads = []
        self.uploaded_zip_entries = []

    def upload_file(self, source_path, bucket_name, s3_key):
        self.uploads.append((bucket_name, s3_key))
        with zipfile.ZipFile(source_path, "r") as zipf:
            self.uploaded_zip_entries = sorted(zipf.namelist())


class _UncommittedHandler:
    def __init__(self):
        self.committed = []

    def on_committed_series(self, series_id):
        self.committed.append(series_id)


class CopySeriesToS3Tests(unittest.TestCase):
    def _make_manager(self, local_storage, s3_client=None, uncommitted_handler=None):
        return LocalToS3ZipManager(
            s3_client=s3_client or _UploadS3Client(),
            bucket_name="bucket",
            local_storage=local_storage,
            enable_compression=False,
            uncommitted_series_handler=uncommitted_handler or _UncommittedHandler(),
            s3_retrieval_retry_base_delay_sec=0,
            s3_retrieval_retry_max_delay_sec=0,
        )

    def test_copy_series_to_s3_leases_source_folder_and_writes_marker_atomically(self):
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            s3_client = _UploadS3Client()
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, s3_client, uncommitted_handler)

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0
            )
            set_custom_data_calls = []

            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    with mock.patch.object(
                        orthanc_stub,
                        "SetAttachmentCustomData",
                        side_effect=lambda uuid, data: set_custom_data_calls.append((uuid, data)),
                    ):
                        manager.copy_series_to_s3("orthanc-series")

            self.assertEqual(local_storage.reads, [("a", "series"), ("b", "series")])
            self.assertGreaterEqual(local_storage.max_lease_depth, 1)
            self.assertEqual(local_storage.lease_depth, 0)
            self.assertEqual(s3_client.uploads, [("bucket", "orthanc-series.zip")])
            self.assertEqual(s3_client.uploaded_zip_entries, ["a", "b"])
            self.assertEqual([uuid for uuid, _ in set_custom_data_calls], ["a", "b"])
            self.assertEqual(uncommitted_handler.committed, ["orthanc-series"])
            marker_path = os.path.join(root, "series", ".s3-uploaded")
            with open(marker_path, "r") as f:
                self.assertEqual(f.read(), "orthanc-series.zip")

    def test_copy_series_with_no_attachment_acknowledges_without_uploading(self):
        # A series deleted between the enqueue and the dequeue comes back
        # from /tools/find with no instances at all. Both fast-path guards
        # below are conditioned on a non-empty attachment list, so without a
        # dedicated exit this used to build an EMPTY zip, PUT it to S3 under
        # the series' key, then fail on the unset local_series_folder --
        # re-enqueueing forever and writing a junk object every cycle.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            s3_client = _UploadS3Client()
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, s3_client, uncommitted_handler)

            with mock.patch.object(manager, "_get_instances_attachments", return_value=[]):
                manager.copy_series_to_s3("vanished-series")

            self.assertEqual(s3_client.uploads, [])
            # The KVS entry is cleared, so the housekeeper stops re-scheduling it.
            self.assertEqual(uncommitted_handler.committed, ["vanished-series"])

    def test_copy_skips_marker_when_new_instance_arrives_during_copy(self):
        # Recheck-before-marker: if a new attachment appears between the
        # initial snapshot and the marker write, the uploaded zip is already
        # incomplete and the marker must NOT be published. The next stable
        # event will trigger a fresh copy that captures the new instance.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, uncommitted_handler=uncommitted_handler)

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0
            )

            # First call: initial snapshot. Second call (the recheck): a third
            # attachment has appeared.
            attachment_calls = [["a", "b"], ["a", "b", "c"]]

            with mock.patch.object(manager, "_get_instances_attachments", side_effect=attachment_calls):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    manager.copy_series_to_s3("orthanc-series")

            # Snapshot's instances were still uploaded + custom-data'd: the
            # snapshot's own data is valid in S3. Only the marker is withheld.
            self.assertEqual(local_storage.reads, [("a", "series"), ("b", "series")])
            self.assertFalse(
                os.path.exists(os.path.join(root, "series", ".s3-uploaded")),
                "marker must not be written when attachment set changed during copy",
            )
            # And the uncommitted-series entry STAYS. Instance "c" is still
            # local-only, so this series is exactly the kind the housekeeper
            # exists to rescue; clearing the entry here would retire that
            # safety net and leave the series' completion resting entirely on
            # a STABLE_SERIES event that may never come (a pod restart between
            # this copy and the stability timer is enough).
            self.assertEqual(uncommitted_handler.committed, [])

    def test_whole_series_gone_is_recorded_as_lost_and_acknowledged(self):
        # Fast-path guard: not one attachment has a local file and none was
        # ever uploaded -- the whole series is gone (a pod restart on an
        # ephemeral volume is the usual cause). The copy must NOT raise (that
        # re-enqueues the worker forever), must upload nothing, and must leave
        # a durable record of the loss: that record is what the status
        # endpoint reads and therefore what stops the Gap Server processing
        # the study.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            local_storage.has_local_file = lambda uuid, local_series_folder, content_type: False
            s3_client = _UploadS3Client()
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, s3_client, uncommitted_handler)

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )

            stored_kvs = []
            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    with mock.patch.object(
                        orthanc_stub, "StoreKeyValue",
                        side_effect=lambda store, key, value: stored_kvs.append((store, key, value)),
                    ):
                        # Must return, not raise.
                        manager.copy_series_to_s3("orthanc-series")

            # Nothing uploaded, no marker written, no reads attempted.
            self.assertEqual(s3_client.uploads, [])
            self.assertEqual(local_storage.reads, [])
            self.assertFalse(os.path.exists(os.path.join(root, "series", ".s3-uploaded")))
            # The loss is recorded where it can be found and reported.
            self.assertEqual([store for store, _, _ in stored_kvs], [LOST_DATA_KVS])
            recorded = json.loads(stored_kvs[0][2].decode("utf-8"))
            self.assertEqual(sorted(recorded["lost_uuids"]), ["a", "b"])
            # KVS bookkeeping cleared so the housekeeper does not loop on it.
            self.assertEqual(uncommitted_handler.committed, ["orthanc-series"])

    def test_a_partially_uploaded_series_with_nothing_local_is_not_waved_through(self):
        # The dangerous middle case, and the reason the guard asks "are they
        # ALL covered?" rather than "is ANY of them covered?".
        #
        # A series was uploaded, then one more instance arrived, then the local
        # folder went away (a pod restart on an ephemeral volume, say). Now
        # nothing is on disk, most attachments carry an S3 zip key, and the
        # late one carries none. "Any of them has a key" reads that as the
        # ordinary evicted-after-upload state and skips quietly -- so the loss
        # is never recorded, and a study missing an instance sails through the
        # storage gate looking exactly like a healthy one.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            local_storage.has_local_file = lambda uuid, local_series_folder, content_type: False
            s3_client = _UploadS3Client()
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, s3_client, uncommitted_handler)

            on_s3 = CustomData(
                storage=CustomData.Storage.S3_ZIP,
                local_series_folder="series",
                s3_zip_key="orthanc-series.zip",
                series_id="orthanc-series",
                size_in_bytes=0,
            )
            never_uploaded = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )
            custom_data = {"a": on_s3, "b": on_s3, "late": never_uploaded}

            stored_kvs = []
            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b", "late"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment",
                                       side_effect=lambda attachment_uuid: custom_data[attachment_uuid]):
                    with mock.patch.object(
                        orthanc_stub, "StoreKeyValue",
                        side_effect=lambda store, key, value: stored_kvs.append((store, key, value)),
                    ):
                        manager.copy_series_to_s3("orthanc-series")

            self.assertEqual(s3_client.uploads, [])
            self.assertEqual([store for store, _, _ in stored_kvs], [LOST_DATA_KVS],
                             "the late instance is on no disk and in no zip: that is a loss")
            recorded = json.loads(stored_kvs[0][2].decode("utf-8"))
            self.assertEqual(recorded["lost_uuids"], ["late"])

    def test_unrecordable_loss_stays_on_the_housekeeper_list(self):
        # The lost-data record IS the alarm: the status endpoint reads it, and
        # that is what makes the Gap Server refuse the study. If the write
        # fails, the series must stay on the housekeeper's list so a later
        # pass tries again -- dropping it would leave a destroyed instance
        # with nothing but a log line behind it.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            local_storage.has_local_file = lambda uuid, local_series_folder, content_type: False
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, uncommitted_handler=uncommitted_handler)

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )

            def failing_store(store, key, value):
                raise RuntimeError("postgres is having a moment")

            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    with mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=failing_store):
                        manager.copy_series_to_s3("orthanc-series")

            self.assertEqual(uncommitted_handler.committed, [],
                             "a loss we could not record must not be forgotten")

    def test_copy_withholds_marker_when_disk_holds_a_file_the_zip_does_not(self):
        # THE regression test for the data loss in QM-9901's e2e run.
        #
        # Orthanc calls the storage area's Create BEFORE it commits the
        # attachment row, so /tools/find can still answer "same 32 attachments
        # as your snapshot" while instance 33's bytes are already sitting in
        # the folder. The copy used to trust that answer, publish the marker,
        # and hand eviction permission to delete a file that exists in no zip
        # anywhere -- which is precisely what happened at 08:06:27 that day.
        #
        # So the marker decision is made against the DISK: an unexplained file
        # in the folder withholds the marker even when the index says nothing
        # changed.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, uncommitted_handler=uncommitted_handler)

            folder = os.path.join(root, "series")
            os.makedirs(folder)
            for uuid in ("a", "b"):
                with open(os.path.join(folder, uuid), "wb") as f:
                    _ = f.write(b"x")
            # Instance "c": on disk, not yet visible to /tools/find.
            with open(os.path.join(folder, "c"), "wb") as f:
                _ = f.write(b"x")

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )

            # Both the snapshot and the recheck report only a and b.
            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    manager.copy_series_to_s3("orthanc-series")

            self.assertFalse(
                os.path.exists(os.path.join(folder, ".s3-uploaded")),
                "marker must be withheld while the folder holds a file the zip does not cover",
            )
            # ... and the housekeeper keeps this series on its books.
            self.assertEqual(uncommitted_handler.committed, [])

    def test_copy_publishes_marker_when_the_folder_matches_the_zip(self):
        # The other half of the disk-based precondition: a folder whose files
        # are exactly what we uploaded (plus the marker machinery itself) must
        # still become evictable, or nothing ever drains the cache.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, uncommitted_handler=uncommitted_handler)

            folder = os.path.join(root, "series")
            os.makedirs(folder)
            for uuid in ("a", "b"):
                with open(os.path.join(folder, uuid), "wb") as f:
                    _ = f.write(b"x")
            # Leftover marker bookkeeping must not be mistaken for instance data.
            with open(os.path.join(folder, ".s3-uploaded.tmp-999-999"), "w") as f:
                _ = f.write("stale")

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )

            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    manager.copy_series_to_s3("orthanc-series")

            with open(os.path.join(folder, ".s3-uploaded"), "r") as f:
                self.assertEqual(f.read(), "orthanc-series.zip")
            self.assertEqual(uncommitted_handler.committed, ["orthanc-series"])

    def test_a_series_that_lost_an_instance_is_never_partially_uploaded(self):
        # THE rule for a damaged series, and it is a clinical one rather than a
        # technical one: this is neurosurgical imaging, so an archive that
        # silently omits an instance is worse than no archive at all. Everything
        # downstream -- the archive endpoint, a later rehydration, an operator
        # looking at the bucket -- would treat that zip as the series.
        #
        # So one unrecoverable attachment abandons the WHOLE series: nothing is
        # uploaded, no marker is published (the surviving instances stay on disk
        # rather than being made evictable), the loss is recorded durably, and
        # the copy returns instead of raising -- raising would re-enqueue the
        # series forever and starve every other series of the single worker.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            s3_client = _UploadS3Client()
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, s3_client, uncommitted_handler)

            folder = os.path.join(root, "series")
            os.makedirs(folder)
            for uuid in ("a", "c"):
                with open(os.path.join(folder, uuid), "wb") as f:
                    _ = f.write(b"x")

            # "b" is the destroyed one: read_file raises and its custom data
            # carries no s3_zip_key, so there is nothing to rehydrate from.
            def read_file(uuid, local_series_folder):
                if uuid == "b":
                    raise FileNotFoundError(uuid)
                return f"content-{uuid}".encode("ascii")

            local_storage.read_file = read_file

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )

            set_custom_data_calls = []
            stored_kvs = []
            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b", "c"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    with mock.patch.object(
                        orthanc_stub,
                        "SetAttachmentCustomData",
                        side_effect=lambda uuid, data: set_custom_data_calls.append(uuid),
                    ):
                        with mock.patch.object(
                            orthanc_stub,
                            "StoreKeyValue",
                            side_effect=lambda store, key, value: stored_kvs.append((store, key, value)),
                        ):
                            # Must NOT raise: raising is what spun the queue.
                            manager.copy_series_to_s3("orthanc-series")

            # NOTHING was uploaded, and no attachment was told it lives in S3.
            self.assertEqual(s3_client.uploads, [])
            self.assertEqual(s3_client.uploaded_zip_entries, [])
            self.assertEqual(set_custom_data_calls, [])
            # No marker: the folder keeps its surviving instances instead of
            # becoming evictable. Cache space is the cheaper thing to lose.
            self.assertFalse(os.path.exists(os.path.join(folder, ".s3-uploaded")))
            # The loss is recorded where it can be listed and reported, not
            # only in a log line that rotates away.
            self.assertEqual(len(stored_kvs), 1)
            store, key, value = stored_kvs[0]
            self.assertEqual(store, LOST_DATA_KVS)
            self.assertEqual(key, "orthanc-series")
            recorded = json.loads(value.decode("utf-8"))
            self.assertEqual(recorded["lost_attachment_count"], 1)
            self.assertEqual(recorded["lost_uuids"], ["b"])
            # The queue entry is released so the shared copy worker moves on to
            # other series -- a damaged series must not take the pipeline down
            # with it.
            self.assertEqual(uncommitted_handler.committed, ["orthanc-series"])

    def test_copy_refuses_to_overwrite_the_s3_zip_when_nothing_can_be_read(self):
        # The same rule at its extreme: if every attachment is unreadable, an
        # upload would PUT an empty archive over the series' key and turn
        # "some instances are lost" into "the whole series is lost".
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            s3_client = _UploadS3Client()
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, s3_client, uncommitted_handler)

            def read_file(uuid, local_series_folder):
                raise FileNotFoundError(uuid)

            local_storage.read_file = read_file

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )

            stored_kvs = []
            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    with mock.patch.object(
                        orthanc_stub, "StoreKeyValue",
                        side_effect=lambda store, key, value: stored_kvs.append((store, key, value)),
                    ):
                        manager.copy_series_to_s3("orthanc-series")

            self.assertEqual(s3_client.uploads, [])
            self.assertEqual([store for store, _, _ in stored_kvs], [LOST_DATA_KVS])
            self.assertEqual(uncommitted_handler.committed, ["orthanc-series"])

    def test_a_repaired_series_clears_its_lost_data_record(self):
        # Recovery path. The operator re-sends the study, Orthanc overwrites the
        # empty records, and the next copy finds the series whole. The alarm
        # must be retracted then -- a stale record would keep the Gap Server
        # refusing a study that is now complete.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            manager = self._make_manager(local_storage)

            folder = os.path.join(root, "series")
            os.makedirs(folder)
            for uuid in ("a", "b"):
                with open(os.path.join(folder, uuid), "wb") as f:
                    _ = f.write(b"x")

            custom_data = CustomData(
                storage=CustomData.Storage.LOCAL,
                local_series_folder="series",
                size_in_bytes=0,
            )

            deleted = []
            with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
                with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=custom_data):
                    with mock.patch.object(orthanc_stub, "GetKeyValue",
                                           side_effect=lambda store, key: b'{"lost_attachment_count": 1}'):
                        with mock.patch.object(orthanc_stub, "DeleteKeyValue",
                                               side_effect=lambda store, key: deleted.append((store, key))):
                            manager.copy_series_to_s3("orthanc-series")

            # The marker was published (the folder matches the zip) ...
            self.assertTrue(os.path.exists(os.path.join(folder, ".s3-uploaded")))
            # ... so the series is whole again and the alarm is retracted.
            self.assertEqual(deleted, [(LOST_DATA_KVS, "orthanc-series")])

    def test_evicted_after_upload_is_not_reported_as_data_loss(self):
        # "no local data left" is the NORMAL end state of a series: uploaded,
        # marked, evicted. Judging loss on local files alone made the copy
        # thread log "data is lost" at ERROR for 14 healthy series in one CI
        # run -- an alert that describes a data-loss incident that did not
        # happen. The s3_zip_key is what separates the two cases.
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            local_storage.has_local_file = lambda uuid, local_series_folder, content_type: False
            s3_client = _UploadS3Client()
            uncommitted_handler = _UncommittedHandler()
            manager = self._make_manager(local_storage, s3_client, uncommitted_handler)

            on_s3 = CustomData(
                storage=CustomData.Storage.S3_ZIP,
                local_series_folder="series",
                s3_zip_key="orthanc-series.zip",
                series_id="orthanc-series",
                size_in_bytes=0,
            )

            with self.assertLogs("s3zip.local_to_s3_zip_manager") as captured:
                with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
                    with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=on_s3):
                        manager.copy_series_to_s3("orthanc-series")

            self.assertEqual(s3_client.uploads, [], "an evicted-but-safe series must not be rebuilt")
            self.assertEqual(uncommitted_handler.committed, ["orthanc-series"])
            self.assertFalse(
                [line for line in captured.output if "ERROR" in line],
                f"a safely-uploaded series must not log an error: {captured.output}",
            )

    def test_backing_off_series_does_not_hold_up_the_other_series(self):
        # The retry backoff used to be a sleep on the single copy worker, so
        # one sick series throttled EVERY series' upload to one per 30 s --
        # and with uploads stalled, nothing becomes evictable and the cache
        # stops draining. The backoff is now per series and enforced at
        # dequeue time: a series still in backoff goes back to the end of the
        # queue and the worker moves on.
        local_storage = _CopyLocalStorage("/nonexistent")
        manager = self._make_manager(local_storage)

        queue_values = ["sick-series", "healthy-series"]
        enqueued = []
        acknowledged = []
        copied = []

        def reserve(queue_name, origin, lease_timeout):
            if not queue_values:
                return None, None
            value = queue_values.pop(0)
            return value.encode("utf-8"), f"value-of-{value}"

        # "sick-series" failed a moment ago and is not due for another 30 s.
        manager._copy_retry_not_before["sick-series"] = time.monotonic() + 30

        with mock.patch.object(orthanc_stub, "ReserveQueueValue", side_effect=reserve):
            with mock.patch.object(orthanc_stub, "EnqueueValue",
                                   side_effect=lambda q, v: enqueued.append(v)):
                with mock.patch.object(orthanc_stub, "AcknowledgeQueueValue",
                                       side_effect=lambda q, v: acknowledged.append(v)):
                    with mock.patch.object(manager, "copy_series_to_s3",
                                           side_effect=lambda series_id: copied.append(series_id)):
                        started = time.monotonic()
                        manager._copy_thread_worker_once()   # sick-series: deferred
                        manager._copy_thread_worker_once()   # healthy-series: copied
                        elapsed = time.monotonic() - started

        self.assertEqual(copied, ["healthy-series"])
        self.assertEqual(enqueued, [b"sick-series"], "the deferred series must go back on the queue")
        self.assertEqual(acknowledged, ["value-of-sick-series", "value-of-healthy-series"])
        self.assertLess(elapsed, 5, "the healthy series must not wait out the sick one's backoff")

    def test_repeated_deferrals_sleep_instead_of_spinning(self):
        # A queue holding nothing but backing-off series must not become a hot
        # dequeue/re-enqueue loop.
        local_storage = _CopyLocalStorage("/nonexistent")
        manager = self._make_manager(local_storage)
        manager._copy_retry_not_before["sick-series"] = time.monotonic() + 30
        manager._consecutive_deferrals = _COPY_QUEUE_MAX_DEFERRALS_BEFORE_IDLE - 1

        slept = []

        with mock.patch.object(orthanc_stub, "ReserveQueueValue",
                               side_effect=lambda *a: (b"sick-series", "value-1")):
            with mock.patch.object(orthanc_stub, "EnqueueValue", side_effect=lambda q, v: None):
                with mock.patch.object(orthanc_stub, "AcknowledgeQueueValue",
                                       side_effect=lambda q, v: None):
                    with mock.patch("local_to_s3_zip_manager.time.sleep", side_effect=slept.append):
                        manager._copy_thread_worker_once()

        self.assertEqual(slept, [_COPY_QUEUE_IDLE_SLEEP_SECONDS])
        self.assertEqual(manager._consecutive_deferrals, 0)

    def test_series_status_reports_lost_attachments_that_sampling_cannot_see(self):
        # is_stored_in_s3 is read from ONE attachment's custom data, and a
        # destroyed attachment is precisely the one that keeps its LOCAL
        # custom data while every other attachment moves to S3_ZIP. Sampling
        # therefore calls a mutilated series whole -- which is what the Gap
        # Server's "is this study durable yet?" gate ultimately reads.
        local_storage = _CopyLocalStorage("/nonexistent")
        manager = self._make_manager(local_storage)

        on_s3 = CustomData(
            storage=CustomData.Storage.S3_ZIP,
            local_series_folder="series",
            s3_zip_key="orthanc-series.zip",
            series_id="orthanc-series",
            size_in_bytes=0,
        )

        record = json.dumps({
            "series_id": "orthanc-series",
            "lost_attachment_count": 2,
            "lost_uuids": ["b", "d"],
            "detected_at_epoch_ms": 1,
        }).encode("utf-8")

        with mock.patch.object(manager, "_get_instances_attachments", return_value=["a", "b"]):
            with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=on_s3):
                with mock.patch.object(orthanc_stub, "GetKeyValue",
                                       side_effect=lambda store, key: record):
                    status = manager.get_series_info("orthanc-series")

        self.assertTrue(status.is_stored_in_s3)
        self.assertEqual(status.lost_attachment_count, 2)

    def test_series_status_reports_no_loss_for_a_healthy_series(self):
        local_storage = _CopyLocalStorage("/nonexistent")
        manager = self._make_manager(local_storage)

        on_s3 = CustomData(
            storage=CustomData.Storage.S3_ZIP,
            local_series_folder="series",
            s3_zip_key="orthanc-series.zip",
            series_id="orthanc-series",
            size_in_bytes=0,
        )

        with mock.patch.object(manager, "_get_instances_attachments", return_value=["a"]):
            with mock.patch.object(CustomData, "from_orthanc_attachment", return_value=on_s3):
                with mock.patch.object(orthanc_stub, "GetKeyValue",
                                       side_effect=lambda store, key: b""):
                    status = manager.get_series_info("orthanc-series")

        self.assertTrue(status.is_stored_in_s3)
        self.assertEqual(status.lost_attachment_count, 0)

    def test_invalidate_s3_uploaded_marker_removes_existing_marker(self):
        with tempfile.TemporaryDirectory() as root:
            local_storage = _CopyLocalStorage(root)
            manager = self._make_manager(local_storage)

            folder = os.path.join(root, "series")
            os.makedirs(folder)
            marker_path = os.path.join(folder, ".s3-uploaded")
            with open(marker_path, "w") as f:
                _ = f.write("series.zip")

            self.assertTrue(manager.invalidate_s3_uploaded_marker("series"))
            self.assertFalse(os.path.exists(marker_path))

            # Idempotent on missing marker.
            self.assertFalse(manager.invalidate_s3_uploaded_marker("series"))


class _FakeKVS:
    """Minimal in-memory backing for orthanc.{Store,Delete}KeyValue + iterator.

    Test fixtures wire its methods onto ``orthanc_stub`` for the duration
    of a test via ``mock.patch.object``.
    """

    def __init__(self):
        self._stores: dict = {}

    def store(self, name, key, value):
        self._stores.setdefault(name, {})[key] = value

    def delete(self, name, key):
        bucket = self._stores.get(name)
        if bucket is not None:
            bucket.pop(key, None)

    def iterator(self, name):
        items = list(self._stores.get(name, {}).items())

        class _Iter:
            def __init__(self, items):
                self._items = items
                self._i = -1
                self._cur = None

            def Next(self):
                self._i += 1
                if self._i >= len(self._items):
                    return False
                self._cur = self._items[self._i]
                return True

            def GetKey(self):
                return self._cur[0]

            def GetValue(self):
                return self._cur[1]

        return _Iter(items)

    def all(self, name):
        return dict(self._stores.get(name, {}))


def _make_bare_s3zip_storage(zip_manager=None, uncommitted_handler=None, local_storage=None):
    """Build a S3ZipStorage skeleton without invoking __init__.

    The full constructor wants a real S3 client, temp folder, etc. The
    housekeeper tests only exercise the methods that touch the KVS, the
    zip manager, and (for the rescue probe) the local storage. We attach
    the minimum needed attributes by hand.
    """
    storage = S3ZipStorage.__new__(S3ZipStorage)
    storage._zip_manager = zip_manager or mock.MagicMock()
    storage._uncommitted_series_handler = uncommitted_handler or mock.MagicMock()
    storage._local_storage = local_storage or mock.MagicMock()
    storage._housekeeper_enabled = True
    storage._housekeeper_interval_sec = 60.0
    storage._housekeeper_timer = None
    storage._housekeeper_stopping = False
    storage._housekeeper_skip_counts = {}
    return storage


def _far_deadline() -> float:
    """A pass deadline that will never be hit during a unit test."""
    return time.monotonic() + 3600.0


class HousekeeperResilienceTests(unittest.TestCase):
    """Resilience properties of the housekeeper passes.

    Focus: a single bad entry MUST NOT break the rest of the run, and the
    timer MUST be re-armed on every exit path.
    """

    def test_perform_housekeeping_reschedules_even_when_pass_raises(self):
        storage = _make_bare_s3zip_storage()
        captured_timers = []

        def fake_timer(interval, fn):
            timer = mock.MagicMock()
            captured_timers.append((interval, fn, timer))
            return timer

        with mock.patch.object(storage, "_perform_housekeeping", side_effect=RuntimeError("boom")):
            with mock.patch("s3_zip_storage.threading.Timer", side_effect=fake_timer):
                storage.perform_housekeeping()

        # The timer must have been re-armed for the next pass.
        self.assertEqual(len(captured_timers), 1)
        self.assertIs(storage._housekeeper_timer, captured_timers[0][2])
        captured_timers[0][2].start.assert_called_once()

    def test_deleted_series_pass_continues_past_corrupt_kvs_value(self):
        kvs = _FakeKVS()
        # Two entries: one corrupt, one valid (its CD points to a series
        # that is gone, so the housekeeper should delete the S3 zip).
        kvs.store(DELETED_SERIES_KVS, "corrupt", b"\x01\x02not-a-customdata\xff")
        valid_cd = CustomData(
            storage=CustomData.Storage.S3_ZIP,
            local_series_folder="folder-of-gone",
            s3_zip_key="prefix/gone.zip",
            series_id="gone",
            size_in_bytes=0,
        ).to_binary()
        kvs.store(DELETED_SERIES_KVS, "gone", valid_cd)

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = None  # really gone, no re-upload race
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        def fake_rest_api_get(uri):
            # Both lookups answer "series no longer exists"
            raise _OrthancException(_ErrorCode.UNKNOWN_RESOURCE)

        with mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator), \
             mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete), \
             mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store), \
             mock.patch.object(orthanc_stub, "RestApiGet", side_effect=fake_rest_api_get):
            storage._housekeep_deleted_series(deadline=_far_deadline())

        # The corrupt entry was dropped (so we don't loop on it forever)
        # and the valid entry was processed (S3 delete called, then KVS
        # entry dropped). Both entries are gone from the KVS.
        self.assertEqual(kvs.all(DELETED_SERIES_KVS), {})
        zip_manager.delete_zip_from_s3.assert_called_once_with(s3_zip_key="prefix/gone.zip")

    def test_deleted_series_pass_isolates_failing_s3_delete(self):
        kvs = _FakeKVS()
        for series_id in ("a", "b", "c"):
            cd = CustomData(
                storage=CustomData.Storage.S3_ZIP,
                local_series_folder=f"folder-{series_id}",
                s3_zip_key=f"prefix/{series_id}.zip",
                series_id=series_id,
                size_in_bytes=0,
            ).to_binary()
            kvs.store(DELETED_SERIES_KVS, series_id, cd)

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = None

        deleted_keys = []

        def flaky_delete(s3_zip_key):
            if s3_zip_key.endswith("/b.zip"):
                raise ConnectionError("transient S3 hiccup")
            deleted_keys.append(s3_zip_key)

        zip_manager.delete_zip_from_s3.side_effect = flaky_delete

        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        def fake_rest_api_get(uri):
            raise _OrthancException(_ErrorCode.UNKNOWN_RESOURCE)

        with mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator), \
             mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete), \
             mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store), \
             mock.patch.object(orthanc_stub, "RestApiGet", side_effect=fake_rest_api_get):
            storage._housekeep_deleted_series(deadline=_far_deadline())

        # 'a' and 'c' were processed; 'b' raised and remains in the KVS
        # for the next pass to retry.
        self.assertEqual(set(deleted_keys), {"prefix/a.zip", "prefix/c.zip"})
        remaining = kvs.all(DELETED_SERIES_KVS)
        self.assertEqual(set(remaining.keys()), {"b"})

    def test_deleted_series_pass_reuploads_when_series_reappears(self):
        # The narrow race: Orthanc says UNKNOWN_RESOURCE, we delete the S3
        # zip, but during the delete a new series with the same series_id
        # got uploaded. Re-query, see the new s3-zip CustomData, and
        # schedule_copy_series_to_s3 to replace the zip we just clobbered.
        kvs = _FakeKVS()
        cd_bytes = CustomData(
            storage=CustomData.Storage.S3_ZIP,
            local_series_folder="folder",
            s3_zip_key="prefix/raced.zip",
            series_id="raced",
            size_in_bytes=0,
        ).to_binary()
        kvs.store(DELETED_SERIES_KVS, "raced", cd_bytes)

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = mock.Mock(
            is_stored_in_s3=True,
            s3_zip_key="prefix/raced.zip",
        )

        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        # /series/<id>/instances says "no" (the housekeeper's check ran
        # before the new upload completed).
        def fake_rest_api_get(uri):
            raise _OrthancException(_ErrorCode.UNKNOWN_RESOURCE)

        with mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator), \
             mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete), \
             mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store), \
             mock.patch.object(orthanc_stub, "RestApiGet", side_effect=fake_rest_api_get):
            storage._housekeep_deleted_series(deadline=_far_deadline())

        zip_manager.delete_zip_from_s3.assert_called_once_with(s3_zip_key="prefix/raced.zip")
        zip_manager.schedule_copy_series_to_s3.assert_called_once_with(series_id="raced")


class HousekeeperUncommittedRescueTests(unittest.TestCase):
    """The 2nd housekeeper pass: rescue or quarantine uncommitted series."""

    def _patch_orthanc(self, kvs, instances_by_series, custom_data_by_attachment,
                       missing_series=(), find_calls=None):
        """Context-manager soup that wires the orthanc stub for one test.

        ``instances_by_series`` maps a series id to the list of instances the
        probe should see, in the shape ``/tools/find`` returns them::

            {"stuck": [{"ID": "i1", "Attachments": [
                {"ContentType": 1, "Uuid": "att1"}]}]}

        The probe is a single bulk ``RestApiPost("/tools/find")`` with
        ``ParentSeries``; ``/series/<id>/instances`` is still used to decide
        whether the series exists at all.
        """
        def fake_rest_api_get(uri):
            # /series/<id>/instances -- existence + emptiness check
            if uri.startswith("/series/") and uri.endswith("/instances"):
                series_id = uri[len("/series/"):-len("/instances")]
                if series_id in missing_series:
                    raise _OrthancException(_ErrorCode.UNKNOWN_RESOURCE)
                return json.dumps(instances_by_series.get(series_id, []))
            raise AssertionError(f"unexpected RestApiGet uri: {uri}")

        def fake_rest_api_post(uri, body):
            if uri != "/tools/find":
                raise AssertionError(f"unexpected RestApiPost uri: {uri}")
            payload = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
            if find_calls is not None:
                find_calls.append(payload)
            series_id = payload.get("ParentSeries")
            if series_id in missing_series:
                return json.dumps([])
            instances = instances_by_series.get(series_id, [])
            limit = payload.get("Limit")
            if limit:
                instances = instances[:limit]
            return json.dumps(instances)

        def fake_get_attachment_custom_data(attachment_uuid):
            cd = custom_data_by_attachment.get(attachment_uuid)
            if cd is None:
                return b""
            return cd.to_binary()

        return [
            mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator),
            mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete),
            mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store),
            mock.patch.object(orthanc_stub, "RestApiGet", side_effect=fake_rest_api_get),
            mock.patch.object(orthanc_stub, "RestApiPost", side_effect=fake_rest_api_post),
            mock.patch.object(orthanc_stub, "GetAttachmentCustomData", side_effect=fake_get_attachment_custom_data),
        ]

    @staticmethod
    def _instance(instance_id: str, *attachment_uuids: str, content_type: int = 1):
        return {
            "ID": instance_id,
            "Attachments": [
                {"ContentType": content_type, "Uuid": a_uuid} for a_uuid in attachment_uuids
            ],
        }

    def test_young_uncommitted_entry_is_left_alone(self):
        kvs = _FakeKVS()
        # Just registered "now": well under the 5-minute grace period.
        now_ms = int(time.time() * 1000)
        kvs.store(UNCOMMITTED_SERIES_KVS, "fresh-series", str(now_ms))

        zip_manager = mock.MagicMock()
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        patches = self._patch_orthanc(
            kvs,
            instances_by_series={"fresh-series": [self._instance("i1", "att1")]},
            custom_data_by_attachment={},  # not consulted -- too young
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        zip_manager.schedule_copy_series_to_s3.assert_not_called()
        self.assertEqual(set(kvs.all(UNCOMMITTED_SERIES_KVS).keys()), {"fresh-series"})

    def test_old_uncommitted_with_local_file_reschedules_copy(self):
        kvs = _FakeKVS()
        old_ms = int(time.time() * 1000) - (10 * 60 * 1000)  # 10 min ago, well past grace
        kvs.store(UNCOMMITTED_SERIES_KVS, "stuck-series", str(old_ms))

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = mock.Mock(is_stored_in_s3=False)
        local_storage = mock.MagicMock()
        local_storage.has_local_file.return_value = True
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager, local_storage=local_storage)

        cd = CustomData(
            storage=CustomData.Storage.LOCAL,
            local_series_folder="folder-of-stuck",
            size_in_bytes=0,
        )
        patches = self._patch_orthanc(
            kvs,
            instances_by_series={"stuck-series": [self._instance("i1", "att1")]},
            custom_data_by_attachment={"att1": cd},
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        zip_manager.schedule_copy_series_to_s3.assert_called_once_with(series_id="stuck-series")
        # Entry stays in KVS -- on_committed_series clears it once the copy
        # actually finishes.
        self.assertEqual(set(kvs.all(UNCOMMITTED_SERIES_KVS).keys()), {"stuck-series"})

    def test_old_uncommitted_without_local_file_still_schedules_copy_with_error(self):
        # Per the design: housekeeper always triggers the copy. The copy
        # thread's fast-path guard (tested separately) is what prevents
        # the queue from spinning when no local data is left. Here we
        # only verify the housekeeper-side behaviour.
        kvs = _FakeKVS()
        old_ms = int(time.time() * 1000) - (10 * 60 * 1000)
        kvs.store(UNCOMMITTED_SERIES_KVS, "lost-series", str(old_ms))

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = mock.Mock(is_stored_in_s3=False)
        local_storage = mock.MagicMock()
        local_storage.has_local_file.return_value = False
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager, local_storage=local_storage)

        cd = CustomData(
            storage=CustomData.Storage.LOCAL,
            local_series_folder="folder-of-lost",
            size_in_bytes=0,
        )
        patches = self._patch_orthanc(
            kvs,
            instances_by_series={"lost-series": [self._instance("i1", "att1")]},
            custom_data_by_attachment={"att1": cd},
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        # Copy IS scheduled (the copy thread's guard will handle the abandon).
        zip_manager.schedule_copy_series_to_s3.assert_called_once_with(series_id="lost-series")
        # The KVS entry stays put -- on_committed_series (called from
        # the copy thread's guard) is the path that clears it.
        self.assertEqual(set(kvs.all(UNCOMMITTED_SERIES_KVS).keys()), {"lost-series"})

    def test_old_uncommitted_with_partial_local_files_logs_tainted_and_schedules(self):
        # 2 of 3 instances have local files. Housekeeper must:
        #  - log at ERROR severity (tainted), and
        #  - still call schedule_copy_series_to_s3 so the failure is
        #    visible in the copy thread.
        kvs = _FakeKVS()
        old_ms = int(time.time() * 1000) - (10 * 60 * 1000)
        kvs.store(UNCOMMITTED_SERIES_KVS, "tainted-series", str(old_ms))

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = mock.Mock(is_stored_in_s3=False)

        cd = CustomData(
            storage=CustomData.Storage.LOCAL,
            local_series_folder="folder-of-tainted",
            size_in_bytes=0,
        )

        # Only attachments "att1" and "att2" have local files; "att3" does not.
        present_attachments = {"att1", "att2"}
        local_storage = mock.MagicMock()
        local_storage.has_local_file.side_effect = (
            lambda uuid, local_series_folder, content_type: uuid in present_attachments
        )
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager, local_storage=local_storage)

        patches = self._patch_orthanc(
            kvs,
            instances_by_series={"tainted-series": [
                self._instance("i1", "att1"),
                self._instance("i2", "att2"),
                self._instance("i3", "att3"),
            ]},
            custom_data_by_attachment={"att1": cd, "att2": cd, "att3": cd},
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        zip_manager.schedule_copy_series_to_s3.assert_called_once_with(series_id="tainted-series")

    def test_old_uncommitted_already_on_s3_clears_stale_entry(self):
        kvs = _FakeKVS()
        old_ms = int(time.time() * 1000) - (10 * 60 * 1000)
        kvs.store(UNCOMMITTED_SERIES_KVS, "already-on-s3", str(old_ms))

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = mock.Mock(
            is_stored_in_s3=True, s3_zip_key="prefix/already-on-s3.zip",
        )
        uncommitted_handler = mock.MagicMock()
        storage = _make_bare_s3zip_storage(
            zip_manager=zip_manager,
            uncommitted_handler=uncommitted_handler,
        )

        patches = self._patch_orthanc(
            kvs,
            instances_by_series={"already-on-s3": [self._instance("i1", "att1")]},
            custom_data_by_attachment={},  # unused -- get_series_info short-circuits
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        uncommitted_handler.on_committed_series.assert_called_once_with(series_id="already-on-s3")
        zip_manager.schedule_copy_series_to_s3.assert_not_called()

    def test_old_uncommitted_series_gone_from_orthanc_drops_entry(self):
        kvs = _FakeKVS()
        old_ms = int(time.time() * 1000) - (10 * 60 * 1000)
        kvs.store(UNCOMMITTED_SERIES_KVS, "deleted-series", str(old_ms))

        storage = _make_bare_s3zip_storage()

        patches = self._patch_orthanc(
            kvs,
            instances_by_series={},
            custom_data_by_attachment={},
            missing_series=("deleted-series",),
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        # Entry dropped because the series is gone -- nothing to do.
        self.assertEqual(kvs.all(UNCOMMITTED_SERIES_KVS), {})

    def test_uncommitted_pass_isolates_failing_entry(self):
        kvs = _FakeKVS()
        old_ms = int(time.time() * 1000) - (10 * 60 * 1000)
        kvs.store(UNCOMMITTED_SERIES_KVS, "blow-up", str(old_ms))
        kvs.store(UNCOMMITTED_SERIES_KVS, "ok-series", str(old_ms))

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.side_effect = lambda series_id: (
            mock.Mock(is_stored_in_s3=False) if series_id == "ok-series" else (_ for _ in ()).throw(RuntimeError("kaboom"))
        )
        local_storage = mock.MagicMock()
        local_storage.has_local_file.return_value = True
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager, local_storage=local_storage)

        cd = CustomData(
            storage=CustomData.Storage.LOCAL,
            local_series_folder="folder",
            size_in_bytes=0,
        )

        patches = self._patch_orthanc(
            kvs,
            instances_by_series={
                "blow-up": [self._instance("i-blow", "att-blow")],
                "ok-series": [self._instance("i-ok", "att-ok")],
            },
            custom_data_by_attachment={"att-blow": cd, "att-ok": cd},
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        # Despite one entry blowing up in get_series_info, the other was
        # still rescued.
        zip_manager.schedule_copy_series_to_s3.assert_called_once_with(series_id="ok-series")


def _deleted_series_entry(series_id: str) -> bytes:
    return CustomData(
        storage=CustomData.Storage.S3_ZIP,
        local_series_folder=f"folder-{series_id}",
        s3_zip_key=f"prefix/{series_id}.zip",
        series_id=series_id,
        size_in_bytes=0,
    ).to_binary()


class HousekeeperLostDataRecordTests(unittest.TestCase):
    """The 3rd housekeeper pass: keep the lost-data KVS honest.

    The record is what makes the host application refuse an incomplete study,
    so it must survive as long as the damaged series does -- and not one pass
    longer. Two reasons, and the second is the sharp one:

      * a damaged series that is deleted rather than repaired has no other
        exit, so its record would accumulate forever;
      * Orthanc series IDs are derived from the DICOM UIDs, so deleting a
        study and re-sending it later yields the SAME series id. A record left
        behind by the deleted series would then condemn the fresh one.
    """

    def _patch_orthanc(self, kvs, existing_series):
        def fake_rest_api_get(uri):
            if uri.startswith("/series/") and uri.endswith("/instances"):
                series_id = uri[len("/series/"):-len("/instances")]
                if series_id not in existing_series:
                    raise _OrthancException(_ErrorCode.UNKNOWN_RESOURCE)
                return json.dumps(existing_series[series_id])
            raise AssertionError(f"unexpected RestApiGet uri: {uri}")

        return [
            mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator),
            mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete),
            mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store),
            mock.patch.object(orthanc_stub, "RestApiGet", side_effect=fake_rest_api_get),
        ]

    def _run(self, kvs, existing_series):
        storage = _make_bare_s3zip_storage()
        with contextlib.ExitStack() as stack:
            for p in self._patch_orthanc(kvs, existing_series):
                stack.enter_context(p)
            return storage._housekeep_lost_data_records(deadline=_far_deadline())

    def test_record_of_a_deleted_series_is_dropped(self):
        kvs = _FakeKVS()
        kvs.store(LOST_DATA_KVS, "gone-series", b'{"lost_attachment_count": 1}')

        processed = self._run(kvs, existing_series={})

        self.assertEqual(processed, 1)
        self.assertEqual(kvs.all(LOST_DATA_KVS), {})

    def test_record_of_a_live_series_is_kept(self):
        # The series is still in Orthanc and still damaged: the record is the
        # only thing standing between an incomplete study and the workflow.
        kvs = _FakeKVS()
        kvs.store(LOST_DATA_KVS, "damaged-series", b'{"lost_attachment_count": 2}')

        processed = self._run(kvs, existing_series={"damaged-series": [{"ID": "i1"}]})

        self.assertEqual(processed, 1)
        self.assertEqual(list(kvs.all(LOST_DATA_KVS)), ["damaged-series"])

    def test_record_of_an_empty_series_is_dropped(self):
        # A series with no instances left has nothing to be missing.
        kvs = _FakeKVS()
        kvs.store(LOST_DATA_KVS, "emptied-series", b'{"lost_attachment_count": 1}')

        self._run(kvs, existing_series={"emptied-series": []})

        self.assertEqual(kvs.all(LOST_DATA_KVS), {})

    def test_an_unexpected_orthanc_error_keeps_the_record(self):
        # "I could not ask" is not "the series is gone". Deleting on a
        # transient failure would throw away the only durable trace of a
        # destroyed instance.
        kvs = _FakeKVS()
        kvs.store(LOST_DATA_KVS, "unknown-state", b'{"lost_attachment_count": 1}')

        storage = _make_bare_s3zip_storage()

        def fake_rest_api_get(uri):
            raise _OrthancException(_ErrorCode.PLUGIN)

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator))
            stack.enter_context(mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete))
            stack.enter_context(mock.patch.object(orthanc_stub, "RestApiGet", side_effect=fake_rest_api_get))
            storage._housekeep_lost_data_records(deadline=_far_deadline())

        self.assertEqual(list(kvs.all(LOST_DATA_KVS)), ["unknown-state"])

    def test_pass_is_bounded_like_the_others(self):
        # No new machinery: the same bounded, resumable batch every other pass
        # uses, so a long list of damaged series cannot turn one tick into an
        # unbounded amount of work.
        kvs = _FakeKVS()
        for i in range(_HOUSEKEEPER_MAX_SERIES_PER_PASS + 5):
            kvs.store(LOST_DATA_KVS, f"series-{i}", b'{"lost_attachment_count": 1}')

        processed = self._run(kvs, existing_series={})

        self.assertEqual(processed, _HOUSEKEEPER_MAX_SERIES_PER_PASS)
        self.assertEqual(len(kvs.all(LOST_DATA_KVS)), 5)

    def test_a_failing_entry_does_not_stop_the_pass(self):
        kvs = _FakeKVS()
        kvs.store(LOST_DATA_KVS, "blow-up", b'{"lost_attachment_count": 1}')
        kvs.store(LOST_DATA_KVS, "gone-series", b'{"lost_attachment_count": 1}')

        storage = _make_bare_s3zip_storage()

        def fake_rest_api_get(uri):
            if "blow-up" in uri:
                raise RuntimeError("kaboom")
            raise _OrthancException(_ErrorCode.UNKNOWN_RESOURCE)

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator))
            stack.enter_context(mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete))
            stack.enter_context(mock.patch.object(orthanc_stub, "RestApiGet", side_effect=fake_rest_api_get))
            processed = storage._housekeep_lost_data_records(deadline=_far_deadline())

        self.assertEqual(processed, 2)
        self.assertEqual(list(kvs.all(LOST_DATA_KVS)), ["blow-up"])


class HousekeeperWorkBudgetTests(unittest.TestCase):
    """The housekeeper must cost the same per tick no matter how big the backlog is.

    The situations that stop KVS entries from being retired (S3 unreachable,
    DeleteObject denied, copy queue backed up) are the same situations that
    make the KVS big -- so an unbounded pass does the most work exactly when
    the Gap Server can least afford it.
    """

    @staticmethod
    def _gone_from_orthanc(uri):
        raise _OrthancException(_ErrorCode.UNKNOWN_RESOURCE)

    def _run_deleted_pass(self, kvs, storage):
        with mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator), \
             mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete), \
             mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store), \
             mock.patch.object(orthanc_stub, "RestApiGet", side_effect=self._gone_from_orthanc):
            return storage._housekeep_deleted_series(deadline=_far_deadline())

    def test_deleted_pass_processes_at_most_one_budget_per_run(self):
        kvs = _FakeKVS()
        total = _HOUSEKEEPER_MAX_SERIES_PER_PASS * 3
        for i in range(total):
            kvs.store(DELETED_SERIES_KVS, f"s{i:04d}", _deleted_series_entry(f"s{i:04d}"))

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = None
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        processed = self._run_deleted_pass(kvs, storage)

        self.assertEqual(processed, _HOUSEKEEPER_MAX_SERIES_PER_PASS)
        self.assertEqual(zip_manager.delete_zip_from_s3.call_count,
                         _HOUSEKEEPER_MAX_SERIES_PER_PASS)
        self.assertEqual(len(kvs.all(DELETED_SERIES_KVS)),
                         total - _HOUSEKEEPER_MAX_SERIES_PER_PASS)

    def test_permanently_failing_entries_cannot_monopolise_successive_passes(self):
        # The scenario that motivated the budget: the leading entries can
        # never be retired (revoked DeleteObject permission, say). Without
        # rotation, every pass would spend its whole budget on the same
        # doomed entries and the rest of the KVS would never be looked at.
        budget = _HOUSEKEEPER_MAX_SERIES_PER_PASS
        kvs = _FakeKVS()
        for i in range(budget * 2):
            kvs.store(DELETED_SERIES_KVS, f"s{i:04d}", _deleted_series_entry(f"s{i:04d}"))

        doomed = {f"prefix/s{i:04d}.zip" for i in range(budget)}
        succeeded = []

        def flaky_delete(s3_zip_key):
            if s3_zip_key in doomed:
                raise PermissionError("AccessDenied: s3:DeleteObject")
            succeeded.append(s3_zip_key)

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = None
        zip_manager.delete_zip_from_s3.side_effect = flaky_delete
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        # Pass 1 burns its whole budget on the doomed head; nothing retires.
        self._run_deleted_pass(kvs, storage)
        self.assertEqual(succeeded, [])
        self.assertEqual(len(kvs.all(DELETED_SERIES_KVS)), budget * 2)

        # Pass 2 resumes past them and drains the healthy tail instead.
        self._run_deleted_pass(kvs, storage)
        self.assertEqual(len(succeeded), budget)
        self.assertEqual(set(kvs.all(DELETED_SERIES_KVS).keys()), {f"s{i:04d}" for i in range(budget)})

        # Pass 3: the resume offset is now past the end of a KVS that only
        # holds the doomed entries. The pass must rewind rather than idle,
        # so the doomed entries do get retried -- forever, but at a flat
        # cost per tick.
        zip_manager.delete_zip_from_s3.reset_mock()
        self._run_deleted_pass(kvs, storage)
        self.assertEqual(zip_manager.delete_zip_from_s3.call_count, budget)

    def test_pass_stops_when_its_time_budget_is_exhausted(self):
        kvs = _FakeKVS()
        for i in range(_HOUSEKEEPER_MAX_SERIES_PER_PASS):
            kvs.store(DELETED_SERIES_KVS, f"s{i:04d}", _deleted_series_entry(f"s{i:04d}"))

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = None
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        with mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=kvs.iterator), \
             mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=kvs.delete), \
             mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store), \
             mock.patch.object(orthanc_stub, "RestApiGet", side_effect=self._gone_from_orthanc):
            processed = storage._housekeep_deleted_series(deadline=time.monotonic() - 1.0)

        self.assertEqual(processed, 0)
        zip_manager.delete_zip_from_s3.assert_not_called()
        # Nothing was retired, so nothing is lost: a later pass picks them up.
        self.assertEqual(len(kvs.all(DELETED_SERIES_KVS)), _HOUSEKEEPER_MAX_SERIES_PER_PASS)

    def test_kvs_iterator_is_released_before_any_entry_is_deleted(self):
        # The pass deletes from the very KVS it walks. Orthanc's iterator is
        # a live PostgreSQL cursor, so the read must be finished (and the
        # transaction closed) before the slow, mutating part starts.
        kvs = _FakeKVS()
        for i in range(3):
            kvs.store(DELETED_SERIES_KVS, f"s{i:04d}", _deleted_series_entry(f"s{i:04d}"))

        call_log = []

        def logging_iterator(name):
            inner = kvs.iterator(name)

            class _Logged:
                def Next(self):
                    call_log.append("next")
                    return inner.Next()

                def GetKey(self):
                    return inner.GetKey()

                def GetValue(self):
                    return inner.GetValue()

            return _Logged()

        def logging_delete(name, key):
            call_log.append("delete")
            return kvs.delete(name, key)

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = None
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager)

        with mock.patch.object(orthanc_stub, "CreateKeysValuesIterator", side_effect=logging_iterator), \
             mock.patch.object(orthanc_stub, "DeleteKeyValue", side_effect=logging_delete), \
             mock.patch.object(orthanc_stub, "StoreKeyValue", side_effect=kvs.store), \
             mock.patch.object(orthanc_stub, "RestApiGet", side_effect=self._gone_from_orthanc):
            storage._housekeep_deleted_series(deadline=_far_deadline())

        self.assertIn("delete", call_log)
        last_read = len(call_log) - 1 - call_log[::-1].index("next")
        first_delete = call_log.index("delete")
        self.assertLess(last_read, first_delete,
                        "the KVS iterator was still being read while entries were deleted")

    def test_probe_bounds_the_instances_it_inspects(self):
        # One huge series must not be able to blow the whole pass: the probe
        # asks Orthanc for a bounded page and decides on that sample.
        kvs = _FakeKVS()
        old_ms = int(time.time() * 1000) - (10 * 60 * 1000)
        kvs.store(UNCOMMITTED_SERIES_KVS, "huge-series", str(old_ms))

        oversize = _HOUSEKEEPER_MAX_INSTANCES_PROBED_PER_SERIES + 250
        instances = [
            HousekeeperUncommittedRescueTests._instance(f"i{i}", f"att{i}")
            for i in range(oversize)
        ]
        cd = CustomData(
            storage=CustomData.Storage.LOCAL,
            local_series_folder="folder-of-huge",
            size_in_bytes=0,
        )

        zip_manager = mock.MagicMock()
        zip_manager.get_series_info.return_value = mock.Mock(is_stored_in_s3=False)
        local_storage = mock.MagicMock()
        local_storage.has_local_file.return_value = True
        storage = _make_bare_s3zip_storage(zip_manager=zip_manager, local_storage=local_storage)

        find_calls = []
        patches = HousekeeperUncommittedRescueTests._patch_orthanc(
            HousekeeperUncommittedRescueTests,
            kvs,
            instances_by_series={"huge-series": instances},
            custom_data_by_attachment={f"att{i}": cd for i in range(oversize)},
            find_calls=find_calls,
        )
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            storage._housekeep_uncommitted_series(deadline=_far_deadline())

        self.assertEqual([c.get("Limit") for c in find_calls],
                         [_HOUSEKEEPER_MAX_INSTANCES_PROBED_PER_SERIES])
        # The verdict is made on the capped sample, not on all 750 instances.
        self.assertEqual(local_storage.has_local_file.call_count,
                         _HOUSEKEEPER_MAX_INSTANCES_PROBED_PER_SERIES)
        zip_manager.schedule_copy_series_to_s3.assert_called_once_with(series_id="huge-series")


class HousekeeperShutdownTests(unittest.TestCase):
    """stop() must actually stop the housekeeper, and not hold up the pod."""

    def _capture_timers(self):
        captured = []

        def fake_timer(interval, fn):
            timer = mock.MagicMock()
            timer.daemon = False
            captured.append(timer)
            return timer

        return captured, fake_timer

    def test_stop_during_a_pass_is_not_undone_by_the_reschedule(self):
        # perform_housekeeping() clears _housekeeper_timer as it starts, so a
        # stop() landing mid-pass has nothing to cancel. If the finally block
        # re-armed unconditionally the housekeeper would survive stop() for
        # the life of the process.
        storage = _make_bare_s3zip_storage()
        captured, fake_timer = self._capture_timers()

        def stop_midway():
            storage._housekeeper_stopping = True

        with mock.patch.object(storage, "_perform_housekeeping", side_effect=stop_midway):
            with mock.patch("s3_zip_storage.threading.Timer", side_effect=fake_timer):
                storage.perform_housekeeping()

        self.assertEqual(captured, [])

    def test_stop_during_a_failing_pass_is_also_honoured(self):
        storage = _make_bare_s3zip_storage()
        captured, fake_timer = self._capture_timers()

        def blow_up_after_stop():
            storage._housekeeper_stopping = True
            raise RuntimeError("boom")

        with mock.patch.object(storage, "_perform_housekeeping", side_effect=blow_up_after_stop):
            with mock.patch("s3_zip_storage.threading.Timer", side_effect=fake_timer):
                storage.perform_housekeeping()

        self.assertEqual(captured, [])

    def test_rescheduled_timer_is_a_daemon_so_sigterm_is_not_delayed(self):
        # A non-daemon Timer keeps the interpreter alive until it fires, so a
        # SIGTERM just after a pass would hold the pod for a full interval.
        storage = _make_bare_s3zip_storage()
        captured, fake_timer = self._capture_timers()

        with mock.patch.object(storage, "_perform_housekeeping"):
            with mock.patch("s3_zip_storage.threading.Timer", side_effect=fake_timer):
                storage.perform_housekeeping()

        self.assertEqual(len(captured), 1)
        self.assertTrue(captured[0].daemon)
        captured[0].start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
