# required: pip install orthanc-tools

from orthanc_api_client import OrthancApiClient
from orthanc_tools import OrthancTestDbPopulator
import time
import boto3
import subprocess
import os
from contextlib import contextmanager

timer_recursion_level=0

@contextmanager
def measure_time(msg: str):
    global timer_recursion_level
    timer_recursion_level += 1
    print(f"{"---" * timer_recursion_level} {msg}: started")
    start_time = time.perf_counter()
    yield
    end_time = time.perf_counter()
    print(f"{"---" * timer_recursion_level} {msg}: {end_time - start_time:.3f} seconds")
    timer_recursion_level -= 1


def wait_until_zip_found_on_s3(series_id: str):
    boto_session = boto3.Session(region_name="eu-west-1",
                                 aws_access_key_id="minio",
                                 aws_secret_access_key="miniopwd")
    s3_client = boto_session.client('s3', 
                                    endpoint_url="http://localhost:9000",
                                    config=boto3.session.Config(s3={'addressing_style': 'path'}))
    
    found = False
    while not found:
        try:
            s3_client.head_object(Bucket="zip-bucket", Key=f"{series_id}.zip")
            return
        except Exception as e:
            pass
        time.sleep(10)


subprocess.run(["docker", "compose", "up", "-d", "--force-recreate"], cwd=os.path.dirname(__file__))

default_orthanc = OrthancApiClient("http://localhost:8052")  # orthanc-s3-default
zip_orthanc = OrthancApiClient("http://localhost:8053")  # orthanc-s3-zip

default_orthanc.wait_started()
zip_orthanc.wait_started()

# TODO: deletion is not yet handled in the s3zip plugin
print("Cleaning default Orthanc")
default_orthanc.delete_all_content()
print("Cleaning zip Orthanc")
zip_orthanc.delete_all_content()

instances_per_series=20
series_count=4
default_populator = OrthancTestDbPopulator(api_client=default_orthanc,
                                           studies_count=1,
                                           series_count=series_count,
                                           instances_count=instances_per_series,
                                           worker_threads_count=5)

zip_populator = OrthancTestDbPopulator(api_client=zip_orthanc,
                                       studies_count=1,
                                       series_count=series_count,
                                       instances_count=instances_per_series,
                                       worker_threads_count=5)

with measure_time("Upload study to S3 default Orthanc (as seen from the REST Api)"):
    default_populator.execute()

with measure_time("Upload study to S3 zip Orthanc (including 5s stable-age + zip + upload zip)"):
    with measure_time("Upload study to S3 zip Orthanc (as seen from the REST Api)"):
        zip_populator.execute()

    all_series_ids = zip_orthanc.series.get_all_ids()
    for series_id in all_series_ids:
        wait_until_zip_found_on_s3(series_id)


print("Cleaning S3 zip local storage to force zip Orthanc to download the file from S3 again")
subprocess.run(["docker", "exec", "python-s3-zip-orthanc-s3-zip-1", "bash", "-c", "rm /tmp-local-storage/*"])

print("Stopping both Orthanc to clear the storage caches")

subprocess.run(["docker", "compose", "down"], cwd=os.path.dirname(__file__))

print("Restarting both Orthanc")
subprocess.run(["docker", "compose", "up", "-d", "--force-recreate"], cwd=os.path.dirname(__file__))

with measure_time("Downloading study from S3 default Orthanc (as seen from the REST Api)"):
    default_orthanc.studies.download_archive(orthanc_id=default_orthanc.studies.get_all_ids()[0],
                                             path="/tmp/default.zip")

with measure_time("Downloading study from S3 zip Orthanc (as seen from the REST Api)"):
    zip_orthanc.studies.download_archive(orthanc_id=zip_orthanc.studies.get_all_ids()[0],
                                         path="/tmp/zip.zip")
