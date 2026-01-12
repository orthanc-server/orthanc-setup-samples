import orthanc
import json
import os
import re
import boto3
import uuid
from typing import Tuple, Optional
from s3_zip_storage import S3ZipStorage

from typing import Optional

# This file contains a wrapper to facilitate the installation of the S3ZipStorage.
# E.g, it implements the singleton pattern and provides global function that can be registered as callbacks in Orthanc.
# The real business logic is inside S3ZipStorage.


storage_singleton: Optional[S3ZipStorage] = None

def _storage_create(uuid: str, 
                    content_type: orthanc.ContentType, 
                    compression_type: orthanc.CompressionType, 
                    content: bytes, 
                    dicom_instance: orthanc.DicomInstance) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    return storage_singleton.storage_create(uuid=uuid,
                                            content_type=content_type,
                                            compression_type=compression_type,
                                            content=content,
                                            dicom_instance=dicom_instance)

def _storage_read_range(uuid: str, 
                        content_type: orthanc.ContentType, 
                        range_start: int,
                        size: int,
                        custom_data: bytes) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    return storage_singleton.storage_read_range(uuid=uuid,
                                                content_type=content_type,
                                                range_start=range_start,
                                                size=size,
                                                custom_data=custom_data)

def _storage_remove(uuid: str,
                    content_type: orthanc.ContentType,
                    custom_data: bytes) -> orthanc.ErrorCode:
    
    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    return storage_singleton.storage_remove(uuid=uuid,
                                            content_type=content_type,
                                            custom_data=custom_data)


def register_s3_zip_storage_plugin():
    
    global storage_singleton

    orthanc_full_configuration = json.loads(orthanc.GetConfiguration())

    s3_zip_config = orthanc_full_configuration.get('S3Zip')
    if not s3_zip_config:
        raise RuntimeError("No 'S3Zip' section defined in Orthanc configuration")

    s3_temp_folder_root = s3_zip_config.get('LocalTemporaryFolder')

    if not s3_temp_folder_root:
        raise RuntimeError("No 'S3Zip.LocalTemporaryFolder' entry defined in Orthanc configuration")

    # try to initialize the s3 client
    if "Region" not in s3_zip_config:
        raise RuntimeError("No 'S3Zip.Region' entry defined in Orthanc configuration")
    if "BucketName" not in s3_zip_config:
        raise RuntimeError("No 'S3Zip.BucketName' entry defined in Orthanc configuration")
    
    boto_session_args = {
        "region_name": s3_zip_config.get("Region"),
    }
    boto_client_args = {}

    if "Endpoint" in s3_zip_config:
        boto_client_args["endpoint_url"] = s3_zip_config.get("Endpoint")

    if "VirtualAddressing" in s3_zip_config and not s3_zip_config["VirtualAddressing"]:
        boto_client_args["config"] = boto3.session.Config(s3={'addressing_style': 'path'})

    # getting credentials from the Orthanc config file.  Otherwise, we assume boto3 knows where to find the credentials on the system
    if "AccessKey" in s3_zip_config and "SecretKey" in s3_zip_config:
        boto_session_args["aws_access_key_id"] = s3_zip_config["AccessKey"]
        boto_session_args["aws_secret_access_key"] = s3_zip_config["SecretKey"]

    boto_session = boto3.Session(**boto_session_args)
    s3_client = boto_session.client('s3', **boto_client_args)
    bucket_name = s3_zip_config.get("BucketName")

    orthanc.LogInfo(f"S3 client created, check accesses to the bucket '{bucket_name}'")
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except s3_client.exceptions.NoSuchBucket:
        raise RuntimeError(f"S3Zip: Bucket '{bucket_name}' does not exist.")
    except Exception as e:
        raise RuntimeError(f"S3Zip: An Error happened while trying to access bucket '{bucket_name}': {e}.")

    test_path = f"_test-access-rights-{uuid.uuid4()}"

    try:
        # test if we can write a file
        s3_client.put_object(Bucket=bucket_name, Key=test_path, Body=b'test')
    except s3_client.exceptions.AccessDenied:
        raise RuntimeError(f"S3Zip: You do not have permission to WRITE in the bucket '{bucket_name}'.")
    except Exception as e:
        raise RuntimeError(f"S3Zip: An Error happened while trying to validate WRITE access bucket '{bucket_name}': {e}.")

    try:
        # test if we can read a file
        s3_client.get_object(Bucket=bucket_name, Key=test_path)
    except s3_client.exceptions.AccessDenied:
        raise RuntimeError(f"S3Zip: You do not have permission to WRITE in the bucket '{bucket_name}'.")
    except Exception as e:
        raise RuntimeError(f"S3Zip: An Error happened while trying to validate WRITE access bucket '{bucket_name}': {e}.")

    try:
        # test if we can delete a file
        s3_client.delete_object(Bucket=bucket_name, Key=test_path)
    except s3_client.exceptions.AccessDenied:
        raise RuntimeError(f"S3Zip: You do not have permission to DELETE in the bucket '{bucket_name}'.")
    except Exception as e:
        raise RuntimeError(f"S3Zip: An Error happened while trying to validate DELETE access bucket '{bucket_name}': {e}.")


    if not os.path.exists(s3_temp_folder_root):
        os.mkdir(s3_temp_folder_root)
        orthanc.LogInfo(f"S3Zip: created temporary folder: f{s3_temp_folder_root}")
    elif os.path.isdir(s3_temp_folder_root):
        orthanc.LogInfo(f"S3Zip: using existing temporary folder: f{s3_temp_folder_root}")
    else:
        raise RuntimeError(f"Failed to initialize S3ZipStorage.  The path '{s3_temp_folder_root}' exists but is not a directory")


    storage_singleton = S3ZipStorage(temporary_folder_root=s3_temp_folder_root, 
                                     temp_folder_max_size_mb=1024,
                                     s3_client=s3_client, 
                                     bucket_name=bucket_name)

    orthanc.RegisterStorageArea3(_storage_create, _storage_read_range, _storage_remove)


def on_stable_series(series_id: str):

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    storage_singleton.copy_series_to_s3(series_id=series_id)  # TODO: schedule_copy instead of synchronous copy !