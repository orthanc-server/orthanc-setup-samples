# required: pip install orthanc-tools python-on-whales
print ("Starting test scenario for S3 zip plugin benchmark...")

from orthanc_api_client import OrthancApiClient
from orthanc_tools import OrthancTestDbPopulator
import time
import boto3
import sys
import os
import threading
from contextlib import contextmanager
from python_on_whales import DockerClient

print ("modules imported...")

# --- ANSI color-coded log streaming ---

ANSI_COLORS = [
    '\033[96m',  # Cyan
    '\033[92m',  # Green
    '\033[93m',  # Yellow
    '\033[94m',  # Blue
    '\033[95m',  # Magenta
]
ANSI_RESET = '\033[0m'

compose_dir = os.path.dirname(os.path.abspath(__file__))
docker = DockerClient(compose_project_directory=compose_dir)

_log_thread = None
_log_stop_event = threading.Event()

def _stream_logs():
    container_colors = {}
    color_index = 0
    try:
        for container_name, log_chunk in docker.compose.logs(follow=True, stream=True):
            if _log_stop_event.is_set():
                break
            if container_name not in container_colors:
                container_colors[container_name] = ANSI_COLORS[color_index % len(ANSI_COLORS)]
                color_index += 1
            color = container_colors[container_name]
            log_text = log_chunk.decode('utf-8', errors='replace') if isinstance(log_chunk, bytes) else log_chunk
            log_text = log_text.rstrip('\r\n')
            sys.stdout.write(f"{color}{container_name} |{ANSI_RESET} {log_text}\n")
            sys.stdout.flush()
    except Exception:
        pass

def compose_up():
    global _log_thread
    _log_stop_event.clear()
    docker.compose.up(detach=True, force_recreate=True)
    _log_thread = threading.Thread(target=_stream_logs, daemon=True)
    _log_thread.start()

def compose_down():
    _log_stop_event.set()
    docker.compose.down()
    if _log_thread is not None:
        _log_thread.join(timeout=5)

# --- Utilities ---

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


# --- Test scenario ---

compose_up()

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
print(f"Populating both Orthancs (default and zip) with {series_count} series of {instances_per_series} instances each (total {series_count * instances_per_series} instances per Orthanc)")
default_populator = OrthancTestDbPopulator(api_client=default_orthanc,
                                           studies_count=1,
                                           series_count=series_count,
                                           instances_count=instances_per_series,
                                           worker_threads_count=5)
print("Populator 1 initialized...")

zip_populator = OrthancTestDbPopulator(api_client=zip_orthanc,
                                       studies_count=1,
                                       series_count=series_count,
                                       instances_count=instances_per_series,
                                       worker_threads_count=5)
print("Populator 2 initialized...")

with measure_time("Upload study to S3 default Orthanc (as seen from the REST Api)"):
    print("Starting upload to default Orthanc...")
    default_populator.execute()

with measure_time("Upload study to S3 zip Orthanc (including 5s stable-age + zip + upload zip)"):
    with measure_time("Upload study to S3 zip Orthanc (as seen from the REST Api)"):
        print("Starting upload to zip Orthanc...")
        zip_populator.execute()

    print("Waiting until zip file is found on S3 (as seen from the zip Orthanc)...")
    all_series_ids = zip_orthanc.series.get_all_ids()
    for series_id in all_series_ids:
        print(f"Waiting for series {series_id}...")
        wait_until_zip_found_on_s3(series_id)


print("Cleaning S3 zip local storage to force zip Orthanc to download the file from S3 again")
docker.execute("python-s3-zip-orthanc-s3-zip-1", ["bash", "-c", "rm -rf /tmp-local-storage/*"])

print("Stopping both Orthanc to clear the storage caches")
compose_down()

print("Restarting both Orthanc")
compose_up()

default_orthanc.wait_started()
zip_orthanc.wait_started()

with measure_time("Downloading study from S3 default Orthanc (as seen from the REST Api)"):
    default_orthanc.studies.download_archive(orthanc_id=default_orthanc.studies.get_all_ids()[0],
                                             path="/tmp/default.zip")

with measure_time("Downloading study from S3 zip Orthanc (as seen from the REST Api)"):
    zip_orthanc.studies.download_archive(orthanc_id=zip_orthanc.studies.get_all_ids()[0],
                                         path="/tmp/zip.zip")
