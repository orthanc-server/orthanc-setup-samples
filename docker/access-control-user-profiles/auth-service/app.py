from fastapi import FastAPI, Header, HTTPException
import logging
import urllib.parse
import pprint
from models import *
import base64
import jwt
import pytz
from datetime import timedelta
from token_service import TokenService
import os

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# the token service is actually not required here but we keep it as an example
# token_service = TokenService(secret_key=os.environ.get("TOKEN_SECRET_KEY", "change-me-I-am-the-default-secret-key"))

@app.post("/user/get-profile")  # this is a POST and not a GET because we want to same kind of payload as for other routes
def get_user_profile(user_profile_request: UserProfileRequest):
    logging.info(f"get user profile from token '{user_profile_request.token_key}'")

    anonymous_profile = UserProfileResponse(
                name="Anonymous",
                permissions=[],
                authorized_labels=[],
                validity=1
            )
    if user_profile_request.token_key == "Authorization":
        if user_profile_request.token_value.startswith("Basic "):
            b64_user_pwd = user_profile_request.token_value.replace("Basic ", "")
            user_pwd = base64.b64decode(b64_user_pwd).decode('utf-8').split(":")
            user = user_pwd[0]
            # the password has already been checked by Orthanc            

            if user == "admin":
                response = UserProfileResponse(
                    name=user,
                    permissions=[UserPermissions.ALL],
                    validity=60)
                response.authorized_labels = ["*"]
            else:
                response = UserProfileResponse(
                    name=user,
                    permissions=[UserPermissions.ALL], # TODO: review the list of permissions for standard users
                    validity=60)
                response.authorized_labels = [user]

            return response

    return anonymous_profile

# # route to create tokens
# @app.put("/tokens/{token_type}")
# def create_token(token_type: str, request: TokenCreationRequest):
#     try:
#         if request.type is None:
#             request.type = token_type
#         elif request.type != token_type:
#             raise HTTPException(status_code=400, detail="'type' field should match the url segment /tokens/{type}")

#         logging.info("creating token: " + request.json())

#         # transform the validity_duration into an expiration_date
#         if request.expiration_date is None and request.validity_duration is not None:
#             request.expiration_date = (pytz.UTC.localize(datetime.now()) + timedelta(seconds=request.validity_duration)).isoformat()

#         if request.type not in [
#             TokenType.VIEWER_INSTANT_LINK,
#             TokenType.DOWNLOAD_INSTANT_LINK
#             ]:
#             # check in https://github.com/orthanc-team/orthanc-auth-service how to handle other tokens
#             return None

#         response = TokenCreationResponse(
#             request=request,
#             token=token_service.encode_token(request=request),
#             url=None
#         )

#         return response

#     except ValueError as ex:
#         raise HTTPException(status_code=400, detail=str(ex))
#     except Exception as ex:
#         logging.exception(ex)
#         raise HTTPException(status_code=500, detail=str(ex))


# # route called by the Orthanc Authorization plugin to validate a token can access to a resource
# @app.post("/tokens/validate")
# def validate_authorization(request: TokenValidationRequest, token=Header(default=None)):

#     try:
#         logging.info("validating token: " + request.json())

#         if request.token_value and not token:
#             token = request.token_value

#         granted = False
#         if token is not None:  # token may be None for Anonymous requests (no tokens)
#             if not token.startswith("Basic "):
                
#                 if token.startswith("Bearer "):
#                     token = token.replace("Bearer ", "")

#                 decoded_token = token_service.decode_token(token=token)
#                 granted = token_service.is_valid(
#                     token=token,
#                     orthanc_id=request.orthanc_id,
#                     dicom_uid=request.dicom_uid,
#                     server_id=request.server_id
#                 )

#         response = TokenValidationResponse(
#             granted=granted,
#             validity=60
#         )
#         logging.info("validate token: " + response.json())
#         return response

#     except ValueError as ex:
#         raise HTTPException(status_code=400, detail=str(ex))
#     except Exception as ex:
#         logging.exception(ex)
#         raise HTTPException(status_code=500, detail=str(ex))


# # # route called by the Orthanc Authorization plugin to decode a token
# # @app.post("/tokens/decode")
# # def decode_token(request: TokenDecoderRequest):

# #     try:
# #         logging.info("decoding token: " + request.json())

# #         response = token_service.decode_token(
# #             token=request.token_value)

# #         logging.info("decoded token: " + response.json())
# #         return response

# #     except ValueError as ex:
# #         raise HTTPException(status_code=400, detail=str(ex))
# #     except Exception as ex:
# #         logging.exception(ex)
# #         raise HTTPException(status_code=500, detail=str(ex))
