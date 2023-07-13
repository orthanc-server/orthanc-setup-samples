import orthanc
import os
import threading
import queue
import traceback
from typing import Optional
from orthanc_api_client import OrthancApiClient
from s3_study_exporter import S3StudyExporter, S3Configuration
import dataclasses
import datetime
import time
from typing import Optional
import pprint

study_exporter = None
worker_thread = None
study_queue = queue.Queue(1000)

orthanc_api_token = orthanc.GenerateRestApiAuthorizationToken()

# messages posted in the queue to be handled by the worker thread
@dataclasses.dataclass
class StudyToProcess:
    study_id: str
    next_retry_time: Optional[datetime.datetime] = None
    retry_count: int = 0


# read 'secret" from Docker secrets or environment variable
def get_secret(name: str, default_value: Optional[str] = None, accept_no_value: bool = False) -> str:
    # first try to read docker secrets
    secret_file_path = f"/run/secrets/{name}"
    if os.path.exists(secret_file_path) and os.path.isfile(secret_file_path):
        with open(secret_file_path, "rt") as secret_file:
            return secret_file.read().strip()

    # then, try to read from env var
    if os.environ.get(name) is None and default_value is None and not accept_no_value:
       raise ValueError(f"You must define {name} env var or Docker secrets")

    return os.environ.get(name, default=default_value)


# the worker thread main function
def process_studies_from_queue():
    global study_queue
    global study_exporter

    while True:
        study_to_process = study_queue.get()  # block until a message is available

        # repost the message if this is not the right time to process it
        if study_to_process.next_retry_time and datetime.datetime.now() < study_to_process.next_retry_time:
            study_queue.put(study_to_process)
            # make sure we do not cycle too fast when we are reposting messages
            time.sleep(1)
            continue

        try:
            study_exporter.export(study_id=study_to_process.study_id)
        except Exception as ex:
            orthanc.LogWarning(f"Error while processing study {study_to_process.study_id}: {ex}")
            traceback.print_exc()
            pprint.pprint(study_to_process)

            # repost the message for later retry
            study_to_process.retry_count += 1
            retry_delay = min(pow(4, study_to_process.retry_count), 1800)  # exponential delay for retry with a max of 30 min
            study_to_process.next_retry_time = datetime.datetime.now() + datetime.timedelta(seconds=retry_delay)
            study_queue.put(study_to_process)

                               
# callback called by Orthanc core every time a 'change' event occurs
def OnChange(changeType, level, resource):
    global study_exporter
    global worker_thread
    global study_queue

    if changeType == orthanc.ChangeType.ORTHANC_STARTED:

        orthanc_url = "http://localhost:8042"
        orthanc_api = OrthancApiClient(orthanc_root_url=orthanc_url,
                                       api_token=orthanc_api_token)
        aws_access_key_id = get_secret("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = get_secret("AWS_SECRET_ACCESS_KEY")
        bucket = get_secret("S3_BUCKET")
        path_template = get_secret("S3_PATH_TEMPLATE", "{OrthancStudyID}.zip")
        delete_after_export = get_secret("S3_DELETE_AFTER_EXPORT", "false").lower() == "true"
        s3_endpoint = get_secret("S3_ENDPOINT", default_value=None, accept_no_value=True)
        
        study_exporter = S3StudyExporter(orthanc_api=orthanc_api,
                                        s3_config=S3Configuration(aws_access_key_id=aws_access_key_id,
                                                                aws_secret_access_key=aws_secret_access_key,
                                                                bucket=bucket,
                                                                endpoint=s3_endpoint),
                                        path_template=path_template,
                                        delete_after_export=delete_after_export)

        worker_thread = threading.Thread(target=process_studies_from_queue)
        worker_thread.start()

        # handle existing studies at startup ?
        all_studies_ids = orthanc_api.studies.get_all_ids()

        if delete_after_export:
            orthanc.LogWarning(f"Python script started.  There are {len(all_studies_ids)} studies in Orthanc and we will export them now")
            for study_id in all_studies_ids:
                study_queue.put(StudyToProcess(study_id=study_id))
        else:
            orthanc.LogWarning(f"Python script started.  There are {len(all_studies_ids)} studies in Orthanc")
       

    elif changeType == orthanc.ChangeType.STABLE_STUDY:

        orthanc.LogWarning(f"Python script:  queuing study {resource}")
        study_queue.put(StudyToProcess(study_id=resource))

    
orthanc.RegisterOnChangeCallback(OnChange)