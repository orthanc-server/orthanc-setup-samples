from typing import Optional
from pydantic import BaseModel, Field



class AuthValidationRequest(BaseModel):
    dicom_uid: Optional[str] = Field(alias="dicom-uid", default=None)
    orthanc_id: Optional[str] = Field(alias="orthanc-id", default=None)
    token_key: Optional[str] = Field(alias="token-key", default=None)
    token_value: Optional[str] = Field(alias="token-value", default=None)
    level: str
    method: str
    uri: Optional[str] = None


class AuthValidationResponse(BaseModel):
    granted: bool
    validity: int


class UserResponse(BaseModel):
    id: str
    institution: str