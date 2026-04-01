import os
import orthanc
import threading
import subprocess
import queue
import shutil
from typing import Callable, Tuple, Optional
from local_storage_interface import LocalStorageInterface
from collections import deque
from s3zip_logging import get_logger

logger = get_logger(__name__)


class LocalStorage(LocalStorageInterface):


    _root: str
    _max_size: int    # all sizes are in [bytes]
    _available_size: int
    _block_size: int
    _lock: threading.RLock
    _folder_stats: queue.PriorityQueue
    _is_folder_safe_to_evict: Optional[Callable[[str], bool]]

    def __init__(self, root: str, max_size_mb: int):
        self._root = root
        self._max_size = max_size_mb * 1024 * 1024
        self._lock = threading.RLock()
        self._is_folder_safe_to_evict = None

        self._update_local_storage_stats()

        logger.debug("LocalStorage initialized",
                     root=root,
                     max_size_mb=max_size_mb,
                     max_size_bytes=self._max_size)

    def set_eviction_guard(self, is_folder_safe_to_evict: callable):
        """
        - Set a callback that determines if a local series folder is safe to evict.
        - The callback receives the folder name (not the full path) and 
          must return True if the folder's data has been safely backed up to S3.
        - If this callback is not set, all folders are considered safe to evict.
        """
        self._is_folder_safe_to_evict = is_folder_safe_to_evict

    def _update_local_storage_stats(self):
        with self._lock:
            self._available_size = self._max_size
            self._block_size = os.statvfs(self._root).f_frsize

            self._folder_stats = queue.PriorityQueue()

            cmd = ["du", "-b", "--max-depth=1", self._root]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split("\n")

            for line in lines:
                size_str, path = line.split("\t")
                folder_size = int(size_str)
                if path != self._root:
                    last_modified = os.path.getmtime(path)
                    self._available_size -= folder_size
                    self._folder_stats.put((last_modified, path, folder_size))


    def _make_room(self, size: int):
        with self._lock:
            estimated_disk_size = ((size + self._block_size - 1) // self._block_size) * self._block_size

            if estimated_disk_size < self._available_size:
                self._available_size -= estimated_disk_size
                return

            self._update_local_storage_stats()

            # Reclaim space -- evict oldest folders first, but protect folders
            # whose data has not yet been safely backed up to S3.
            # This can be useful if the plugin receives a burst of uploads that
            # exceed the local storage capacity, but the S3 upload process is
            # still catching up
            skipped = []
            while estimated_disk_size > self._available_size and not self._folder_stats.empty():
                entry = self._folder_stats.get()
                _, path, folder_size = entry

                folder_name = os.path.basename(path)

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

                # TODO: handle errors here (e.g. if the file gets locked by
                # another process, or if it is being deleted by someone trying
                # to help! Unlikely but what can go wrong will go wrong...)
                shutil.rmtree(path)
                self._available_size += folder_size

            # put skipped entries back
            for entry in skipped:
                self._folder_stats.put(entry)

            if estimated_disk_size > self._available_size:
                logger.warning(
                    "LocalStorage: could not free enough space. "
                    "Some folders are protected because they are not yet on S3.",
                    needed=estimated_disk_size,
                    available=self._available_size,
                    protected_folders=len(skipped))


    def write_file(self, local_series_folder: str, uuid: str, content: bytes):
        self._make_room(len(content))

        self._write_file(uuid=uuid,
                         local_series_folder=local_series_folder,
                         content_type=orthanc.ContentType.DICOM,
                         content=content)


    def _write_file(self, uuid: str, local_series_folder: str, content_type: orthanc.ContentType, content: bytes):

        path = self.get_local_path(uuid=uuid,
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

        # with self._lock:

        # TODO: increment used_size + LRU references

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

        path = self.get_local_path(uuid=uuid,
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
                data = f.read(size)
            else:
                data = f.read()

        logger.debug("file read from local storage",
                     uuid=uuid,
                     path=path,
                     bytes_read=len(data),
                     range_start=range_start)
        return data


    SUPPORTED_CONTENT_TYPES = (orthanc.ContentType.DICOM, orthanc.ContentType.DICOM_UNTIL_PIXEL_DATA)

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
            data = self._read_file(uuid=uuid,
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
               content_type: orthanc.ContentType):

        # TODO: we should probably implement an asynchronous file deleter

        path = self.get_local_path(uuid=uuid,
                                   local_series_folder=local_series_folder,
                                   content_type=content_type)

        existed = os.path.exists(path)

        if existed:
            os.remove(path)

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
        path = self.get_local_path(uuid=uuid,
                                   local_series_folder=local_series_folder,
                                   content_type=content_type)
        exists = os.path.exists(path)

        logger.debug("has_local_file check",
                     uuid=uuid,
                     local_series_folder=local_series_folder,
                     path=path,
                     exists=exists)
        return exists
