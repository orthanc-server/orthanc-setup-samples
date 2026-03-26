import sys
import orthanc
import json
import os
import boto3
import uuid as uuid_module
from typing import Tuple, Optional
from s3_zip_storage import S3ZipStorage
from s3zip_logging import get_logger

# This file contains a wrapper to facilitate the installation of the S3ZipStorage.
# E.g, it implements the singleton pattern and provides global function that can be registered as callbacks in Orthanc.
# The real business logic is inside S3ZipStorage.

logger = get_logger(__name__)
logger.debug("s3_zip_storage_plugin module loaded")

storage_singleton: Optional[S3ZipStorage] = None


def _storage_create(uuid: str,
                    content_type: orthanc.ContentType,
                    compression_type: orthanc.CompressionType,
                    content: bytes,
                    dicom_instance: orthanc.DicomInstance) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:

    logger.debug("_storage_create handler entered",
                 uuid=uuid,
                 content_type=str(content_type),
                 size_bytes=len(content))

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    logger.debug("_storage_create: delegating to storage_singleton",
                 uuid=uuid,
                 content_type=str(content_type),
                 size_bytes=len(content))

    result = storage_singleton.storage_create(uuid=uuid,
                                              content_type=content_type,
                                              compression_type=compression_type,
                                              content=content,
                                              dicom_instance=dicom_instance)

    logger.debug("_storage_create handler done",
                 uuid=uuid,
                 content_type=str(content_type),
                 size_bytes=len(content),
                 error_code=str(result[0]))
    return result


def _storage_read_range(uuid: str,
                        content_type: orthanc.ContentType,
                        range_start: int,
                        size: int,
                        custom_data: bytes) -> Tuple[orthanc.ErrorCode, Optional[bytes]]:

    logger.debug("_storage_read_range handler entered",
                 uuid=uuid,
                 content_type=str(content_type),
                 range_start=range_start,
                 size=size)

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    logger.debug("_storage_read_range: delegating to storage_singleton",
                 uuid=uuid,
                 content_type=str(content_type),
                 range_start=range_start,
                 size=size)

    result = storage_singleton.storage_read_range(uuid=uuid,
                                                  content_type=content_type,
                                                  range_start=range_start,
                                                  size=size,
                                                  custom_data=custom_data)

    error_code, data = result
    logger.debug("_storage_read_range handler done, returning to Orthanc",
                 uuid=uuid,
                 error_code=str(error_code),
                 bytes_returned=len(data) if data else 0)
    logger.debug("_storage_read_range handler done",
                 uuid=uuid,
                 content_type=str(content_type),
                 range_start=range_start,
                 size=size,
                 error_code=str(error_code),
                 bytes_returned=len(data) if data else 0)
    return result


def _storage_remove(uuid: str,
                    content_type: orthanc.ContentType,
                    custom_data: bytes) -> orthanc.ErrorCode:

    logger.debug("_storage_remove handler entered",
                 uuid=uuid,
                 content_type=str(content_type))

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    logger.debug("_storage_remove: delegating to storage_singleton",
                 uuid=uuid,
                 content_type=str(content_type))

    result = storage_singleton.storage_remove(uuid=uuid,
                                              content_type=content_type,
                                              custom_data=custom_data)

    logger.debug("_storage_remove handler done, returning to Orthanc",
                 uuid=uuid,
                 error_code=str(result))
    logger.debug("_storage_remove handler done",
                 uuid=uuid,
                 content_type=str(content_type),
                 error_code=str(result))
    return result


def on_rest_api_series_s3_status(output, uri, **request):  # GET -> returns a status to know if the series is stored in S3
    global storage_singleton

    if request['method'] == 'GET':
        series_id = request['groups'][0]
        series_status = storage_singleton.get_series_status(series_id=series_id)
        if not series_status:
            logger.error("Failed to retrieve series status", series_id)
            output.SendHttpStatusCode(400)
            return
        
        status = {
            'is-stored-in-s3': series_status.is_stored_in_s3,
            's3-zip-key': series_status.s3_zip_key
        }
        output.AnswerBuffer(json.dumps(status), 'application/json')
    else:
        output.SendMethodNotAllowed('GET')


def on_rest_api_series_s3_archive(output, uri, **request): # GET -> streams a zip from s3 through Orthanc (if not in s3, get it from Orthanc core API (without streaming))
    global storage_singleton
    if request['method'] == 'GET':
        series_id = request['groups'][0]

        series_status = storage_singleton.get_series_status(series_id=series_id)

        output.SetHttpHeader('Content-Disposition', f'filename={series_id}.zip')
        output.StartStreamAnswer('application/zip')

        if series_status.is_stored_in_s3:
            logger.info("streaming series archive from s3")
            zip_stream = storage_singleton.get_s3_zip_stream(series_id=series_id)

            while True:
                chunk = zip_stream.read(64*1024)
                if not chunk:
                    return                

                output.SendStreamChunk(chunk)
        else:
            logger.info("getting series archive from core")
            zip = orthanc.RestApiGet(uri)
            output.SendStreamChunk(zip)

    else:
        output.SendMethodNotAllowed('GET')


def on_rest_api_series_s3_copy_to_s3(output, uri, **request):  # POST, no payload, answer = {} -> schedules a copy to s3 (asynchronous)
    global storage_singleton

    if request['method'] == 'POST':
        series_id = request['groups'][0]
        storage_singleton.schedule_copy_series_to_s3(series_id=series_id)
        status = {}
        output.AnswerBuffer(json.dumps(status), 'application/json')
    else:
        output.SendMethodNotAllowed('POST')



def register_s3_zip_storage_plugin():

    global storage_singleton

    logger.info("S3Zip storage plugin registration starting")

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

    # Determine credential source
    has_explicit_credentials = "AccessKey" in s3_zip_config and "SecretKey" in s3_zip_config
    if has_explicit_credentials:
        boto_session_args["aws_access_key_id"] = s3_zip_config["AccessKey"]
        boto_session_args["aws_secret_access_key"] = s3_zip_config["SecretKey"]

    logger.debug("creating boto3 session",
                 region=s3_zip_config.get("Region"),
                 endpoint=boto_client_args.get("endpoint_url", "<default>"),
                 credential_source="orthanc-config" if has_explicit_credentials else "environment/instance-profile",
                 virtual_addressing=s3_zip_config.get("VirtualAddressing", True))

    logger.debug("calling boto3.Session()")
    boto_session = boto3.Session(**boto_session_args)
    logger.debug("boto3.Session() returned")
    logger.debug("calling boto_session.client('s3')")
    s3_client = boto_session.client('s3', **boto_client_args)
    logger.debug("boto_session.client('s3') returned")
    bucket_name = s3_zip_config.get("BucketName")

    logger.debug("boto3 S3 client created, validating bucket access", bucket=bucket_name)

    # --- validate bucket access ---
    logger.info("validating S3 bucket access", bucket=bucket_name)
    try:
        logger.debug("calling s3_client.head_bucket()", bucket=bucket_name)
        s3_client.head_bucket(Bucket=bucket_name)
        logger.debug("s3_client.head_bucket() returned", bucket=bucket_name)
        logger.debug("head_bucket succeeded", bucket=bucket_name)
    except s3_client.exceptions.NoSuchBucket:
        logger.error("S3 bucket does not exist", bucket=bucket_name)
        raise RuntimeError(f"S3Zip: Bucket '{bucket_name}' does not exist.")
    except Exception as e:
        logger.error("failed to access S3 bucket", bucket=bucket_name, error=str(e))
        raise RuntimeError(f"S3Zip: An Error happened while trying to access bucket '{bucket_name}': {e}.")

    test_path = f"_test-access-rights-{uuid_module.uuid4()}"

    try:
        logger.debug("testing WRITE access to S3 bucket", bucket=bucket_name, test_key=test_path)
        logger.debug("calling s3_client.put_object()", bucket=bucket_name, test_key=test_path)
        s3_client.put_object(Bucket=bucket_name, Key=test_path, Body=b'test')
        logger.debug("s3_client.put_object() returned", bucket=bucket_name)
        logger.debug("WRITE access test succeeded", bucket=bucket_name)
    except Exception as e:
        logger.error("S3 WRITE access test failed", bucket=bucket_name, error=str(e))
        raise RuntimeError(f"S3Zip: WRITE access denied or error for bucket '{bucket_name}': {e}.")

    try:
        logger.debug("testing READ access to S3 bucket", bucket=bucket_name, test_key=test_path)
        logger.debug("calling s3_client.get_object()", bucket=bucket_name, test_key=test_path)
        s3_client.get_object(Bucket=bucket_name, Key=test_path)
        logger.debug("s3_client.get_object() returned", bucket=bucket_name)
        logger.debug("READ access test succeeded", bucket=bucket_name)
    except Exception as e:
        logger.error("S3 READ access test failed", bucket=bucket_name, error=str(e))
        raise RuntimeError(f"S3Zip: READ access denied or error for bucket '{bucket_name}': {e}.")

    try:
        logger.debug("testing DELETE access to S3 bucket", bucket=bucket_name, test_key=test_path)
        logger.debug("calling s3_client.delete_object()", bucket=bucket_name, test_key=test_path)
        s3_client.delete_object(Bucket=bucket_name, Key=test_path)
        logger.debug("s3_client.delete_object() returned", bucket=bucket_name)
        logger.debug("DELETE access test succeeded", bucket=bucket_name)
    except Exception as e:
        logger.error("S3 DELETE access test failed", bucket=bucket_name, error=str(e))
        raise RuntimeError(f"S3Zip: DELETE access denied or error for bucket '{bucket_name}': {e}.")

    logger.info("S3 bucket access validated (read/write/delete)", bucket=bucket_name)

    # --- local temp folder ---
    if not os.path.exists(s3_temp_folder_root):
        os.mkdir(s3_temp_folder_root)
        logger.info("created local temporary folder", folder=s3_temp_folder_root)
    elif os.path.isdir(s3_temp_folder_root):
        logger.debug("using existing local temporary folder", folder=s3_temp_folder_root)
    else:
        logger.error("path exists but is not a directory", folder=s3_temp_folder_root)
        raise RuntimeError(f"Failed to initialize S3ZipStorage.  The path '{s3_temp_folder_root}' exists but is not a directory")

    enable_compression = "EnableCompression" not in s3_zip_config or s3_zip_config.get("EnableCompression")
    if "LocalStorageMaxSizeMB" in s3_zip_config:
        max_local_storage_size_mb = int(s3_zip_config.get("LocalStorageMaxSizeMB"))
    else:
        max_local_storage_size_mb = 1024
    logger.debug("compression setting resolved", enable_compression=enable_compression)

    storage_singleton = S3ZipStorage(temporary_folder_root=s3_temp_folder_root,
                                     temp_folder_max_size_mb=max_local_storage_size_mb,
                                     s3_client=s3_client,
                                     bucket_name=bucket_name,
                                     enable_compression=enable_compression)

    logger.info("registering storage area callbacks with Orthanc (RegisterStorageArea3)")
    logger.debug("calling orthanc.RegisterStorageArea3()")
    orthanc.RegisterStorageArea3(_storage_create, _storage_read_range, _storage_remove)
    logger.debug("orthanc.RegisterStorageArea3() returned")

    logger.debug("registering new REST Api routes")
    orthanc.RegisterRestCallback('/series/(.*)/s3-zip/status', on_rest_api_series_s3_status)
    orthanc.RegisterRestCallback('/series/(.*)/s3-zip/copy-to-s3', on_rest_api_series_s3_copy_to_s3)
    orthanc.RegisterRestCallback('/series/(.*)/archive', on_rest_api_series_s3_archive)
    logger.debug("registering new REST Api routes - done")


    logger.info("S3Zip storage plugin registered SUCCESSFULLY",
                bucket=bucket_name,
                region=s3_zip_config.get("Region"),
                temp_folder=s3_temp_folder_root,
                compression=enable_compression)

    # Failsafe: bypass logging framework entirely so this is always visible
    print(f"[s3zip] storage plugin registered | bucket={bucket_name} "
          f"region={s3_zip_config.get('Region')} temp_folder={s3_temp_folder_root} "
          f"compression={enable_compression}", file=sys.stderr)


def on_stable_series(series_id: str):

    logger.debug("on_stable_series handler entered", series_id=series_id)

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    logger.info("stable series detected, scheduling S3 copy", series_id=series_id)
    storage_singleton.schedule_copy_series_to_s3(series_id=series_id)

    logger.info("on_stable_series handler done, returning to Orthanc", series_id=series_id)


def on_orthanc_started():
    logger.debug("on_orthanc_started handler entered")

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    logger.info("Orthanc started, starting S3Zip manager")
    storage_singleton.start()

    logger.info("on_orthanc_started handler done, returning to Orthanc")


def on_orthanc_stopped():
    logger.debug("on_orthanc_stopped handler entered")

    global storage_singleton
    if not storage_singleton:
        raise RuntimeError("S3ZipStorage has not been initialized.")

    logger.info("Orthanc stopped, stopping S3Zip manager")
    storage_singleton.stop()

    logger.info("on_orthanc_stopped handler done, returning to Orthanc")
