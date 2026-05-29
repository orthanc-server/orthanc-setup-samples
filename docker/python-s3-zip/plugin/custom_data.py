from typing import Optional
from enum import Enum
import json
import orthanc
from s3zip_logging import get_logger

logger = get_logger(__name__)


class CustomData:

    class Storage(str, Enum):
        LOCAL = "local"
        S3_ZIP = "s3-zip"

    storage: Storage
    local_series_folder: str
    s3_zip_key: Optional[str]
    size_in_bytes: int
    series_id: Optional[str]   # this value is not available in the storage_create (when storing in tmp-local-storage).  It only becomes available when the series is moved to s3

    def __init__(self, 
                 storage: Storage, 
                 local_series_folder: str, 
                 size_in_bytes: int,
                 series_id: Optional[str] = None,
                 s3_zip_key: Optional[str] = None):
        self.storage = storage
        self.local_series_folder = local_series_folder
        self.s3_zip_key = s3_zip_key
        self.series_id = series_id
        self.size_in_bytes = size_in_bytes

    def to_binary(self) -> bytes:
        b = self.to_json().encode('utf-8')
        logger.debug("CustomData serialized to binary",
                     storage=self.storage.value,
                     local_series_folder=self.local_series_folder,
                     s3_zip_key=self.s3_zip_key or "<none>",
                     series_id=self.series_id or "<none>",
                     size_in_bytes=self.size_in_bytes,
                     binary_size_bytes=len(b))
        return b

    def to_json(self) -> str:
        return json.dumps({
            "storage": self.storage.value,
            "local": self.local_series_folder,
            "s3zip": self.s3_zip_key,
            "series-id": self.series_id,
            "size": self.size_in_bytes
        })

    @classmethod
    def from_binary(cls, b: bytes) -> 'CustomData':
        logger.debug("CustomData deserializing from binary", binary_size_bytes=len(b))
        return cls.from_json(b.decode('utf-8'))

    @classmethod
    def from_json(cls, json_str: str) -> 'CustomData':
        data = json.loads(json_str)
        required_keys = ("storage", "local", "s3zip", "series-id", "size")
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(
                f"CustomData is missing required key(s): {', '.join(missing_keys)}"
            )
        storage = cls.Storage(data["storage"])
        local_series_folder = data["local"]
        s3_zip_key = data["s3zip"]
        series_id = data["series-id"]
        size_in_bytes = data["size"]

        if not isinstance(local_series_folder, str) or not local_series_folder:
            raise ValueError("CustomData key 'local' must be a non-empty string")
        if s3_zip_key is not None and not isinstance(s3_zip_key, str):
            raise ValueError("CustomData key 's3zip' must be a string or null")
        if series_id is not None and not isinstance(series_id, str):
            raise ValueError("CustomData key 'series-id' must be a string or null")
        if not isinstance(size_in_bytes, int) or size_in_bytes < 0:
            raise ValueError("CustomData key 'size' must be a non-negative integer")
        if storage == cls.Storage.S3_ZIP and not s3_zip_key:
            raise ValueError("CustomData for S3Zip storage must include a non-empty 's3zip' key")
        if storage == cls.Storage.S3_ZIP and not series_id:
            raise ValueError("CustomData for S3Zip storage must include a non-empty 'series-id' key")

        cd = cls(
            storage=storage,
            local_series_folder=local_series_folder,
            s3_zip_key=s3_zip_key,
            series_id=series_id,
            size_in_bytes=size_in_bytes
        )
        logger.debug("CustomData deserialized",
                     storage=cd.storage.value,
                     local_series_folder=cd.local_series_folder,
                     s3_zip_key=cd.s3_zip_key or "<none>",
                     series_id=cd.series_id or "<none>",
                     size_in_bytes=cd.size_in_bytes)
        return cd

    @classmethod
    def from_orthanc_attachment(cls, attachment_uuid: str) -> Optional['CustomData']:
        logger.debug("calling orthanc.GetAttachmentCustomData()", attachment_uuid=attachment_uuid)
        b = orthanc.GetAttachmentCustomData(attachment_uuid)
        if len(b) > 0:
            cd = cls.from_binary(b)
            logger.debug("orthanc.GetAttachmentCustomData() returned",
                        attachment_uuid=attachment_uuid,
                        storage=cd.storage.value,
                        local_series_folder=cd.local_series_folder,
                        s3_zip_key=cd.s3_zip_key or "<none>",
                        series_id=cd.series_id or "<none>",
                        size_in_bytes=cd.size_in_bytes)
            return cd
        else:
            return None
