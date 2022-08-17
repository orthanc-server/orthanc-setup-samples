from typing import Union
from pydantic import BaseModel, Field



class AuthValidationRequest(BaseModel):
    dicom_uid: Union[str, None] = Field(alias="dicom-uid", default=None)
    orthanc_id: Union[str, None] = Field(alias="orthanc-id", default=None)
    token_key: Union[str, None] = Field(alias="token-key", default=None)
    token_value: Union[str, None] = Field(alias="token-value", default=None)
    level: str
    method: str
    uri: Union[str, None]


class AuthValidationResponse(BaseModel):
    granted: bool
    validity: int


class UserResponse(BaseModel):
    id: str
    institution: str