from fastapi import FastAPI, Header
import logging
import urllib.parse
import pprint
from models import *
from orthanc_api_client import OrthancApiClient
import base64

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()
o = OrthancApiClient("http://orthanc-for-admin:8042", user="auth-service-user", pwd="auth-service-pwd")  # the auth-service is using an Orthanc in which we don't check authorization (to avoid looping)

def get_user_institution_name(user_id):
    # this should come from a database !
    if user_id == '1' or user_id == 'key-1':
        institution = 'INST-1'
    elif user_id == '2' or user_id == 'key-2':
        institution = 'INST-2'
    else:
        institution = 'PUBLIC'
    
    return institution

# route called by the Orthanc Authorization plugin to validate a auth_header has access to a resource
@app.post("/auth/validate")
def validate_authorization(validation_request: AuthValidationRequest, auth_header = Header(default=None)):
    logging.info("validating auth request: " + validation_request.json())

    granted = False

    if validation_request.level == "system":
        granted=False

        allowed_system_routes = [
            # routes used by Orthanc Explorer 2 and that do not contain patient data
            "/statistics",
            "/peers",
            "/modalities",
            "/plugins",
            "/ui/api/configuration",
            "/dicom-web/servers",
            "/tools/find",        # tools/find is allowed but we filter the results in the python plugin
            "/dicom-web/studies",  # QIDO-RS endpoint
        ]
        granted = validation_request.uri in allowed_system_routes

    elif validation_request.level == "study":

        if validation_request.token_key.lower() == "authorization":
            user = base64.b64decode(validation_request.token_value.replace("Basic ", "")).decode('utf-8').split(':')[0]
            user_institution = get_user_institution_name(user)
        elif validation_request.token_key.lower() == "api-key":
            user_institution = get_user_institution_name(validation_request.token_value)
        else:
            raise NotImplementedError()

        if validation_request.orthanc_id:
            study = o.studies.get(validation_request.orthanc_id)
        elif validation_request.dicom_uid:
            study = o.studies.find(query={"StudyInstanceUID": validation_request.dicom_uid})
        else:
            raise NotImplementedError()
        study_institution = study.main_dicom_tags["InstitutionName"]

        granted = user_institution == study_institution

    response = AuthValidationResponse(
        granted=granted,
        validity=60
    )

    logging.info("validate auth: " + response.json())
    return response


# route called by the python plugin running in Orthanc to retrieve the InstitutionName from the user id or api-key
@app.get("/users/{user_id}")
def get_user(user_id: str, token = Header(default=None)):
    logging.info("get user info: " + user_id)

    response = UserResponse(
        id=user_id,
        institution=get_user_institution_name(user_id)
    )
    logging.info("get user info: " + response.json())
    return response
