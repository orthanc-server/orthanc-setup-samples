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

    def __init__(self, storage: Storage, local_series_folder: str, s3_zip_key: Optional[str] = None):
        self.storage = storage
        self.local_series_folder = local_series_folder
        self.s3_zip_key = s3_zip_key

    def to_binary(self) -> bytes:
        b = self.to_json().encode('utf-8')
        logger.debug("CustomData serialized to binary",
                     storage=self.storage.value,
                     local_series_folder=self.local_series_folder,
                     s3_zip_key=self.s3_zip_key or "<none>",
                     size_bytes=len(b))
        return b

    def to_json(self) -> str:
        return json.dumps({
            "storage": self.storage.value,
            "local": self.local_series_folder,
            "s3zip": self.s3_zip_key
        })

    @classmethod
    def from_binary(cls, b: bytes) -> 'CustomData':
        logger.debug("CustomData deserializing from binary", size_bytes=len(b))
        return cls.from_json(b.decode('utf-8'))

    @classmethod
    def from_json(cls, json_str: str) -> 'CustomData':
        data = json.loads(json_str)
        cd = cls(
            storage=cls.Storage(data["storage"]),
            local_series_folder=data["local"],
            s3_zip_key=data["s3zip"]
        )
        logger.debug("CustomData deserialized",
                     storage=cd.storage.value,
                     local_series_folder=cd.local_series_folder,
                     s3_zip_key=cd.s3_zip_key or "<none>")
        return cd

    @classmethod
    def from_orthanc_attachment(cls, attachment_uuid: str) -> 'CustomData':
        logger.debug("calling orthanc.GetAttachmentCustomData()", attachment_uuid=attachment_uuid)
        cd = cls.from_binary(orthanc.GetAttachmentCustomData(attachment_uuid))
        logger.debug("orthanc.GetAttachmentCustomData() returned",
                     attachment_uuid=attachment_uuid,
                     storage=cd.storage.value,
                     local_series_folder=cd.local_series_folder,
                     s3_zip_key=cd.s3_zip_key or "<none>")
        return cd