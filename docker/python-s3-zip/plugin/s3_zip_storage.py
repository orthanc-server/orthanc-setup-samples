import orthanc
import os
import json
from helpers import Helpers
from typing import Optional, Tuple
from boto3 import client as S3Client
from local_storage import LocalStorage
from local_to_s3_zip_manager import LocalToS3ZipManager
from custom_data import CustomData



class S3ZipStorage:

    _local_storage: LocalStorage
    _zip_manager: LocalToS3ZipManager

    def __init__(self, temporary_folder_root: str, temp_folder_max_size_mb: int, s3_client: S3Client, bucket_name: str):
        self._local_storage = LocalStorage(root=temporary_folder_root,
                                           max_size_mb=temp_folder_max_size_mb)
        
        self._zip_manager = LocalToS3ZipManager(s3_client=s3_client,
                                                bucket_name=bucket_name,
                                                local_storage=self._local_storage)

    def start(self):
        self._zip_manager.start()

    def stop(self):
        self._zip_manager.stop()

    def storage_create(self,
                       uuid: str, 
                       content_type: orthanc.ContentType, 
                       compression_type: orthanc.CompressionType, 
                       content: bytes, 
                       dicom_instance: orthanc.DicomInstance) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:
        
        series_hash = Helpers.get_series_hash(dicom_instance)

        # we always write only to the local storage
        error_code = self._local_storage.create(uuid=uuid,
                                                local_series_folder=series_hash,
                                                content_type=content_type,
                                                compression_type=compression_type,
                                                content=content)
        
        # return error_code, None  # no need to store custom_data (no custom_data means that the file is stored only in the local storage)
        return error_code, CustomData(CustomData.Storage.LOCAL, local_series_folder=series_hash).to_binary()


    def storage_read_range(self,
                           uuid: str, 
                           content_type: orthanc.ContentType, 
                           range_start: int,
                           size: int,
                           custom_data: bytes) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:

        cd = CustomData.from_binary(custom_data)
        if not self._local_storage.has_local_file(uuid=uuid, 
                                                  local_series_folder=cd.local_series_folder,
                                                  content_type=content_type):  # TODO: implement a LocalFileLocker with __enter__ & __exit__ to make sure the file is not deleted in the meantime
            self._zip_manager.retrieve_zip_from_s3(s3_zip_key=cd.s3_zip_key,
                                                   local_series_folder=cd.local_series_folder)


        # make sure the file is in the local storage (this is a blocking call)
        # TODO

        # if custom_data and len(custom_data):
        #     custom_data = json.loads(custom_data.decode('utf-8'))
        
        return self._local_storage.read_range(uuid=uuid,
                                              local_series_folder=cd.local_series_folder,
                                              content_type=content_type,
                                              range_start=range_start,
                                              size=size)

    def storage_remove(self,
                       uuid: str,
                       content_type: orthanc.ContentType,
                       custom_data: bytes) -> orthanc.ErrorCode:

        # always delete from the local storage in case it has been stored there
        self._local_storage.remove(uuid=uuid,
                                   local_series_folder=CustomData.from_binary(custom_data).local_series_folder,
                                   content_type=content_type)

        # TODO: we should probably mark the file as deleted somehow but, how and when do we remove the zip in S3 ?
        
        return orthanc.ErrorCode.SUCCESS


    def schedule_copy_series_to_s3(self, series_id: str):
        self._zip_manager.schedule_copy_series_to_s3(series_id=series_id)
