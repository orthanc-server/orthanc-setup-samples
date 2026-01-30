from typing import Optional
from enum import Enum
import json
import orthanc


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
        return self.to_json().encode('utf-8')

    def to_json(self) -> str:
        return json.dumps({
            "storage": self.storage.value,
            "local": self.local_series_folder,
            "s3zip": self.s3_zip_key
        })

    @classmethod
    def from_binary(cls, b: bytes) -> 'CustomData':
        return cls.from_json(b.decode('utf-8'))

    @classmethod
    def from_json(cls, json_str: str) -> 'CustomData':
        data = json.loads(json_str)
        return cls(
            storage=cls.Storage(data["storage"]),
            local_series_folder=data["local"],
            s3_zip_key=data["s3zip"]
        )    
    
    @classmethod
    def from_orthanc_attachment(cls, attachment_uuid: str) -> 'CustomData':
        return cls.from_binary(orthanc.GetAttachmentCustomData(attachment_uuid))