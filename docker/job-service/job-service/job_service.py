from fastapi import FastAPI, Request, status, Header, HTTPException, Depends, Query
from typing import Any
import logging
from job_registry import JobRegistry, JobAction, OrthancException

# This FastAPI server implements the job-service API
# The business logic is actually implemented in the JobRegistry


logging.basicConfig(level=logging.DEBUG)


app = FastAPI()
job_registry = JobRegistry()


# debug: log invalid requests/payloads
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.post("/orthanc/started")
async def orthanc_started(request: Request):
    logging.info("Orthanc started on IP: " + request.client.host)
    payload = await request.json()
    job_registry.orthanc_started(orthanc_ip=request.client.host, api_token=payload["api-token"])


@app.post("/orthanc/stopped")
async def orthanc_stopped(request: Request):
    logging.info("Orthanc stopped on IP: " + request.client.host)


@app.post("/jobs/{job_id}/submitted")
async def job_submitted(job_id: str, request: Request):
    logging.info(f"Job {job_id} submitted on IP: " + request.client.host)
    payload = await request.json()
    job_registry.update_job(orthanc_ip=request.client.host,
                            job=payload["job"],
                            api_token=payload["api-token"])

@app.post("/jobs/{job_id}/failure")
async def job_failure(job_id: str, request: Request):
    logging.info(f"Job {job_id} failure on IP: " + request.client.host)
    payload = await request.json()
    job_registry.update_job(orthanc_ip=request.client.host,
                            job=payload["job"],
                            api_token=payload["api-token"])

@app.post("/jobs/{job_id}/success")
async def job_success(job_id: str, request: Request):
    logging.info(f"Job {job_id} success on IP: " + request.client.host)
    payload = await request.json()
    job_registry.update_job(orthanc_ip=request.client.host,
                            job=payload["job"],
                            api_token=payload["api-token"])


@app.post("/jobs/refresh")
async def refresh_jobs(request: Request):
    logging.info(f"Refreshing all jobs")
    job_registry.refresh_all_jobs()

@app.get("/jobs")
async def get_all_jobs(request: Request, status: str | None = None):
    expand = request.query_params.get('expand') is not None

    return job_registry.get_jobs(filter_status=status, expand=expand)


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
	try:
		return job_registry.get_job(job_id=job_id)
	except FileNotFoundError:
		raise HTTPException(status_code=404, detail="Job not found in job-service DB")


@app.post("/jobs/{job_id}/{job_action}")
async def post_job_action(job_id: str, job_action: JobAction):
	try:
		return job_registry.post_job_action(job_id=job_id, job_action=job_action)
	except FileNotFoundError:
		raise HTTPException(status_code=404, detail="Job not found in job-service DB")
	except OrthancException as ex:
		raise HTTPException(status_code=ex.status_code, detail=ex.payload)

# to debug the script locally:
import uvicorn

if __name__ == "__main__":
      uvicorn.run(app, host="0.0.0.0", port=8000)