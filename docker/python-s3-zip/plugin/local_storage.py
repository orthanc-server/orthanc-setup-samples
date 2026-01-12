import os
import orthanc
from typing import Tuple, Optional
from local_storage_interface import LocalStorageInterface


class LocalStorage(LocalStorageInterface):

    _root: str
    _max_size_bytes: int    # TODO: handle max size


    def __init__(self, root: str, max_size_mb: int):
        self._root = root
        self._max_size_bytes = max_size_mb * 1024


    def write_file(self, uuid: str, content: bytes):
        
        self._write_file(uuid=uuid,
                         content_type=orthanc.ContentType.DICOM,
                         content=content)


    def _write_file(self, uuid: str, content_type: orthanc.ContentType, content: bytes):

        path = self.get_local_path(uuid=uuid,
                                   content_type=content_type)
        
        with open(path, "wb") as f:
            f.write(content)
        
        # orthanc.LogInfo(f"Successfully created local file {path} for {uuid}, wrote {len(content)} bytes")

    def read_file(self, uuid: str) -> bytes:
        
        return self._read_file(uuid=uuid,
                               content_type=orthanc.ContentType.DICOM,
                               range_start=0,
                               size=0)

    def _read_file(self, 
                   uuid: str,
                   content_type: orthanc.ContentType, 
                   range_start: int,
                   size: int) -> bytes:

        path = self.get_local_path(uuid=uuid,
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
               content_type: orthanc.ContentType, 
               compression_type: orthanc.CompressionType, 
               content: bytes) -> orthanc.ErrorCode:

        if content_type != orthanc.ContentType.DICOM:
            raise RuntimeError(f"Only DICOM files are supported right now")

        try:
            self.write_file(uuid=uuid,
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
                   content_type: orthanc.ContentType, 
                   range_start: int,
                   size: int) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:


        try:
            data = self._read_file(uuid=uuid,
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
               content_type: orthanc.ContentType):

        # TODO: we should probably implement an asynchronous file deleter

        path = self.get_local_path(uuid=uuid,
                                   content_type=content_type)
        if os.path.exists(path):
            os.remove(path)
            # orthanc.LogInfo(f"Successfully removed file {path} for {uuid}")
            

    def get_local_path(self, uuid: str, content_type: orthanc.ContentType) -> str:

        if content_type != orthanc.ContentType.DICOM:
            raise RuntimeError(f"Only DICOM files are supported right now")

        # this is a flat hierarchy, unlike the orthanc default file system that has 2 levels of intermediate directories
        return os.path.join(self._root, uuid)
    
    def has_local_file(self, uuid: str, content_type: orthanc.ContentType) -> bool:
        return os.path.exists(self.get_local_path(uuid=uuid,
                                                  content_type=content_type))