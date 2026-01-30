import os
import orthanc
import threading
from typing import Tuple, Optional
from local_storage_interface import LocalStorageInterface
from collections import deque


class LocalStorage(LocalStorageInterface):


    _root: str
    _max_size_bytes: int    # TODO: handle max size
    _used_size_bytes: int
    _lock: threading.Lock
    _lru_files: deque

    def __init__(self, root: str, max_size_mb: int):
        self._root = root
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._used_size_bytes = 0
        self._lock = threading.Lock()
        self._lru_files = deque()


    def _make_room(self, size: int):
        with self._lock:
            while self._max_size_bytes - self._used_size_bytes < size:
                file_to_remove = self._lru_files.pop()


    def write_file(self, local_series_folder: str, uuid: str, content: bytes):
        
        self._write_file(uuid=uuid,
                         local_series_folder=local_series_folder, 
                         content_type=orthanc.ContentType.DICOM,
                         content=content)


    def _write_file(self, uuid: str, local_series_folder: str, content_type: orthanc.ContentType, content: bytes):

        path = self.get_local_path(uuid=uuid,
                                   local_series_folder=local_series_folder,
                                   content_type=content_type)
        
        os.makedirs(os.path.dirname(path), exist_ok=True)        

        with open(path, "wb") as f:
            f.write(content)
        
        # with self._lock:

        # TODO: increment used_size + LRU references
        # orthanc.LogInfo(f"Successfully created local file {path} for {uuid}, wrote {len(content)} bytes")

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

        with open(path, "rb") as f:
            if range_start > 0:
                f.seek(range_start)

            if size > 0:
                data = f.read(size)
            else:
                data = f.read()
            
        # orthanc.LogInfo(f"Read {len(data)} bytes from position {range_start}")
        return data


    def create(self,
               uuid: str, 
               local_series_folder: str,
               content_type: orthanc.ContentType, 
               compression_type: orthanc.CompressionType, 
               content: bytes) -> orthanc.ErrorCode:

        if content_type != orthanc.ContentType.DICOM:
            raise RuntimeError(f"Only DICOM files are supported right now")

        try:
            self.write_file(uuid=uuid,
                            local_series_folder=local_series_folder,
                            content=content)

            return orthanc.ErrorCode.SUCCESS
        except IOError as e:
            orthanc.LogError(f"Failed to create storage for {uuid}: {str(e)}")
            return orthanc.ErrorCode.PLUGIN
        except Exception as e:
            orthanc.LogError(f"Unexpected error creating storage for {uuid}: {str(e)}")
            return orthanc.ErrorCode.PLUGIN


    def read_range(self,
                   uuid: str, 
                   local_series_folder: str, 
                   content_type: orthanc.ContentType, 
                   range_start: int,
                   size: int) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:


        try:
            data = self._read_file(uuid=uuid,
                                   local_series_folder=local_series_folder,
                                   content_type=content_type,
                                   range_start=range_start,
                                   size=size)
                
            # orthanc.LogInfo(f"Read {len(data)} bytes from position {range_start}")
            return orthanc.ErrorCode.SUCCESS, data
        except FileNotFoundError:
            orthanc.LogError(f"File not found for {uuid}")
            return orthanc.ErrorCode.UNKNOWN_RESOURCE, None
        except Exception as e:
            orthanc.LogError(f"Error reading file for {uuid}: {str(e)}")
            return orthanc.ErrorCode.PLUGIN, None


    def remove(self,
               uuid: str,
               local_series_folder: str,
               content_type: orthanc.ContentType):

        # TODO: we should probably implement an asynchronous file deleter

        path = self.get_local_path(uuid=uuid,
                                   local_series_folder=local_series_folder,
                                   content_type=content_type)
        if os.path.exists(path):
            os.remove(path)
            # orthanc.LogInfo(f"Successfully removed file {path} for {uuid}")
            

    def get_local_path(self, uuid: str, local_series_folder: str, content_type: orthanc.ContentType) -> str:

        if content_type != orthanc.ContentType.DICOM:
            raise RuntimeError(f"Only DICOM files are supported right now")

        return os.path.join(self._root, os.path.join(local_series_folder, uuid))
    
    def has_local_file(self, uuid: str, local_series_folder: str, content_type: orthanc.ContentType) -> bool:
        return os.path.exists(self.get_local_path(uuid=uuid,
                                                  local_series_folder=local_series_folder,
                                                  content_type=content_type))