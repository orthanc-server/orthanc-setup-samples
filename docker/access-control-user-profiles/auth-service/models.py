# this file comes from https://github.com/orthanc-team/orthanc-auth-service
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class Levels(str, Enum):
    PATIENT = 'patient'
    STUDY = 'study'
    SERIES = 'series'
    INSTANCE = 'instance'

    SYSTEM = 'system'


class Methods(str, Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'


class DecoderErrorCodes(str, Enum):
    EXPIRED = 'expired'
    INVALID = 'invalid'
    UNKNOWN = 'unknown'


class TokenType(str, Enum):
    OSIMIS_VIEWER_PUBLICATION = 'osimis-viewer-publication'  # a link to open the Osimis viewer valid for a long period
    MEDDREAM_VIEWER_PUBLICATION = 'meddream-viewer-publication'  # a link to open the MedDream viewer valid for a long period
    STONE_VIEWER_PUBLICATION = 'stone-viewer-publication'  # a link to open the Stone viewer valid for a long period
    OHIF_VIEWER_PUBLICATION = 'ohif-viewer-publication'  # a link to open the OHIF viewer valid for a long period

    MEDDREAM_INSTANT_LINK = 'meddream-instant-link'  # a direct link to MedDream viewer that is valid only a few minutes to open the viewer directly

    # OSIMIS_VIEWER_INSTANT_LINK = 'osimis-viewer-instant-link'  # a direct link to Osimis viewer that is valid only a few minutes to open the viewer directly
    # STONE_VIEWER_INSTANT_LINK = 'stone-viewer-instant-link'  # a direct link to Stone viewer that is valid only a few minutes to open the viewer directly
    #
    # DOWNLOAD_INSTANT_LINK = 'download-instant-link'  # a link to download a study/series/instance directly
    VIEWER_INSTANT_LINK = 'viewer-instant-link'             # a link to a resource to be used directly.
    DOWNLOAD_INSTANT_LINK = 'download-instant-link'         # a link to a resource to be used directly.


    INVALID = 'invalid'

class OrthancResource(BaseModel):
    dicom_uid: Optional[str] = Field(alias="dicom-uid", default=None)
    orthanc_id: Optional[str] = Field(alias="orthanc-id", default=None)
    url: Optional[str] = None                                                       # e.g. a download link /studies/.../archive
    level: Levels

    class Config:  # allow creating object from dict (used when deserializing the JWT)
        populate_by_name = True


class TokenCreationRequest(BaseModel):
    id: Optional[str] = None
    resources: List[OrthancResource]
    type: TokenType = Field(default=TokenType.INVALID)
    expiration_date: Optional[datetime] = Field(alias="expiration-date", default=None)
    validity_duration: Optional[int] = Field(alias='validity-duration', default=None)            # alternate way to provide an expiration_date, more convenient for instant-links since the duration is relative to the server time, not the client time !

    class Config:  # allow creating object from dict (used when deserializing the JWT)
        populate_by_name = True


class TokenCreationResponse(BaseModel):
    request: TokenCreationRequest
    token: str
    url: Optional[str] = None


class TokenValidationRequest(BaseModel):
    dicom_uid: Optional[str] = Field(alias="dicom-uid", default=None)
    orthanc_id: Optional[str] = Field(alias="orthanc-id", default=None)
    token_key: Optional[str] = Field(alias="token-key", default=None)
    token_value: Optional[str] = Field(alias="token-value", default=None)
    server_id: Optional[str] = Field(alias="server-id", default=None)
    level: Optional[Levels]
    method: Methods
    uri: Optional[str] = None


class TokenValidationResponse(BaseModel):
    granted: bool
    validity: int


class TokenDecoderRequest(BaseModel):
    token_key: Optional[str] = Field(alias="token-key", default=None)
    token_value: Optional[str] = Field(alias="token-value", default=None)


class TokenDecoderResponse(BaseModel):
    token_type: Optional[TokenType] = Field(alias="token-type", default=None)
    error_code: Optional[DecoderErrorCodes] = Field(alias="error-code", default=None)
    redirect_url: Optional[str] = Field(alias="redirect-url", default=None)


class UserProfileRequest(BaseModel):
    token_key: Optional[str] = Field(alias="token-key", default=None)
    token_value: Optional[str] = Field(alias="token-value", default=None)
    server_id: Optional[str] = Field(alias="server-id", default=None)


class UserPermissions(str, Enum):
    ALL = 'all'
    VIEW = 'view'
    DOWNLOAD = 'download'
    DELETE = 'delete'
    SEND = 'send'
    MODIFY = 'modify'
    ANONYMIZE = 'anonymize'
    UPLOAD = 'upload'
    Q_R_REMOTE_MODALITIES = 'q-r-remote-modalities'
    SETTINGS = 'settings'
    API_VIEW = 'api-view'
    EDIT_LABELS = 'edit-labels'
    ADMIN_PERMISSIONS = 'admin-permissions'

    SHARE = 'share'


class RolePermissions(BaseModel):
    authorized_labels: List[str] = Field(alias="authorized-labels", default_factory=list)
    permissions: List[UserPermissions] = Field(default_factory=list)

    class Config:
        use_enum_values = True
        populate_by_name = True  # allow creating object from dict (used when deserializing the permission file)


class UserProfileResponse(RolePermissions):
    name: str
    validity: int

    class Config:
        use_enum_values = True
        populate_by_name = True

class RolesConfigurationModel(BaseModel):
    roles: Dict[str, RolePermissions]                                                    # role/permissions mapping
    available_labels: List[str] = Field(alias="available-labels", default_factory=list)  # if empty, everyone can create additionnal labels, if not, they can only add/remove the listed labels
