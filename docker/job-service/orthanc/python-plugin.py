import orthanc
import requests
import os
import json
import pprint


job_service_url = os.environ.get("JOB_SERVICE_URL", "http://job-service:8000")


api_token = orthanc.GenerateRestApiAuthorizationToken()

def OnChange(changeType, level, resource):

    if changeType == orthanc.ChangeType.JOB_SUCCESS:

        orthanc.LogInfo(f"job {resource} has succeeded")

        job = json.loads(orthanc.RestApiGet(f"/jobs/{resource}"))
        requests.post(url=f"{job_service_url}/jobs/{resource}/success", json={
            "api-token": api_token,
            "job": job
        })

    elif changeType == orthanc.ChangeType.JOB_FAILURE:

        orthanc.LogWarning(f"job {resource} has failed")

        job = json.loads(orthanc.RestApiGet(f"/jobs/{resource}"))
        requests.post(url=f"{job_service_url}/jobs/{resource}/failure", json={
            "api-token": api_token,
            "job": job
        })

    elif changeType == orthanc.ChangeType.JOB_SUBMITTED:

        orthanc.LogInfo(f"job {resource} has been submitted")

        job = json.loads(orthanc.RestApiGet(f"/jobs/{resource}"))
        requests.post(url=f"{job_service_url}/jobs/{resource}/submitted", json={
            "api-token": api_token,
            "job": job
        })

    elif changeType == orthanc.ChangeType.ORTHANC_STARTED:

        orthanc.LogWarning(f"orthanc python plugin has started " + f"{job_service_url}/orthanc/started")

        requests.post(url=f"{job_service_url}/orthanc/started", json={"api-token": api_token})

    elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:

        orthanc.LogWarning(f"orthanc python plugin is stopping")

        requests.post(url=f"{job_service_url}/orthanc/stopped")


orthanc.RegisterOnChangeCallback(OnChange)
