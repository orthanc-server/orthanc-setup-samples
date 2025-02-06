from models import *
import urllib
import logging
import jwt
import pytz
from typing import Optional
from json import JSONEncoder


class DateTimeJSONEncoder(JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        

# This class generates JWT tokens that can be used by orthanc to access specific resources
# This is not required in this sample project but it contains a simplified version
# of the Token service from https://github.com/orthanc-team/orthanc-auth-service
class TokenService:

    secret_key_: str

    def __init__(self, secret_key: str):
        self._secret_key = secret_key

    def encode_token(self, request: TokenCreationRequest) -> str:
        return jwt.encode(request.model_dump(), self._secret_key, algorithm="HS256", json_encoder=DateTimeJSONEncoder)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret_key, algorithms="HS256")
        except jwt.exceptions.InvalidTokenError:
            raise ValueError(msg="invalid token")


    def is_expired(self, request: TokenCreationRequest) -> bool:
        # check expiration date
        if request.expiration_date:
            now_utc = pytz.UTC.localize(datetime.now())

            is_valid = now_utc < request.expiration_date
            if not is_valid:
                logging.warning(f"Token Validation: period is invalid")
            return not is_valid

        return False


    def is_valid(self, token: str, orthanc_id: Optional[str] = None, dicom_uid: Optional[str] = None, server_id: Optional[str] = None) -> bool:

        # no ids to check, we consider it's invalid
        if not dicom_uid and not orthanc_id:
            logging.warning(f"Token Validation: no ids found")
            return False

        try:
            r = self.decode_token(token)
            share_request = TokenCreationRequest(**r)
        except Exception as ex:
            logging.warning(f"Token Validation: failed to decode token")
            return False

        granted = False

        # check the ids.  The share_request might have been generated with 2 ids
        share_request_has_dicom_uids = all([s.dicom_uid is not None for s in share_request.resources])
        share_request_has_orthanc_ids = all([s.orthanc_id is not None for s in share_request.resources])
        # but when we check, we'll probably only have a single ID (the orthanc_id for Orthanc Rest API and the dicom_uid for DicomWeb)
        if dicom_uid and share_request_has_dicom_uids:
            granted = any([s.dicom_uid == dicom_uid for s in share_request.resources])
            if not granted:
                all_dicom_uids = ", ".join([s.dicom_uid for s in share_request.resources])
                logging.warning(f"Token Validation: invalid dicom_uid, from request: {dicom_uid}, from token: {all_dicom_uids}")
                return False

        if orthanc_id and share_request_has_orthanc_ids:
            granted = any([s.orthanc_id == orthanc_id for s in share_request.resources])
            if not granted:
                all_orthanc_ids = ", ".join([s.orthanc_id for s in share_request.resources])
                logging.warning(f"Token Validation: invalid orthanc_id, from request: {orthanc_id}, from token: {all_orthanc_ids}")
                return False

        # check expiration date
        granted = granted and not self.is_expired(share_request)

        return granted

