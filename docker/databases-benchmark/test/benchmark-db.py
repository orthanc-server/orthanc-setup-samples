from orthanc_api_client import OrthancApiClient, helpers
from orthanc_tools import OrthancTestDbPopulator

import time
import os
import queue
import threading
import logging
import csv
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import json
import shutil
import zipfile
import tempfile
from urllib.request import urlretrieve


import pathlib
here = pathlib.Path(__file__).parent.resolve()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

generate_snapshots = False
use_snapshots = True
local_tests = True  # True: this scripts runs locally, False: this script runs in a Docker container in the docker compose (uncomment it in docker-compose.yml !!)

# snapshots are available for downloads at https://public-files.orthanc.team/databases-benchmark/pg-18-1000000.tar.gz / sqlite-1000000.zip
# snapshots_sizes = [5000, 10000, 20000, 40000, 60000, 80000, 100000, 200000, 300000, 400000, 500000, 600000, 800000, 1000000]
snapshots_sizes = [5000, 10000, 20000, 40000, 60000, 100000, 200000, 500000, 600000, 1000000]

uploader_threads_count = os.environ.get("UPLOADER_THREADS_COUNT", 5)
instances_queue = queue.Queue(0)
instances_per_step = int(os.environ.get('INSTANCES_PER_STEP', '1000'))
studies_per_step = int(os.environ.get('STUDIES_PER_STEP', '20'))
series_per_studies = int(os.environ.get('SERIES_PER_STUDIES', '5'))

env = os.environ.copy()
env["DOCKER_HOST"] = "unix:///var/run/docker.sock"


if local_tests:
    results_root_path = "../results/"

    test_configs = {
        "docker-sqlite-1.13.0": {
            "orthanc-url": "http://localhost:8143",
            "results": results_root_path + "docker-sqlite-ref.txt",
            "type": "SQLite",
            "container": "orthanc-sqlite-ref",
            "db-volume": "orthanc-storage-sqlite-ref"
        },
                # "docker-pg-11.0": {
                #     "orthanc-url": "http://localhost:8145",
                #     "results": results_root_path + "docker-pg-ref.txt",
                #     "type": "PG",
                #     "container": "orthanc-pg-ref",
                #     "db-container": "pg-ref-db"
                # },
        # "docker-sqlite-next": {
        #     "orthanc-url": "http://localhost:8144",
        #     "results": results_root_path + "docker-sqlite-next.txt",
        #     "type": "SQLite",
        #     "container": "orthanc-sqlite-next",
        #     "db-volume": "orthanc-storage-sqlite-next"
        # },
        # "local-sqlite-1.13.0-LSB-release": {
        #     "orthanc-url": "http://localhost:8046",
        #     "results": results_root_path + "local-sqlite-1.13.0-LSB-release.txt",
        #     "type": "SQLite",
        #     #"exe": "/home/alain/o/build/orthanc-release/Orthanc-with-sqlite-ordering",
        #     "exe": "/home/alain/Releases/Orthanc-1.13.0",
        #     "exe-config-file": "/home/alain/o/build/configs/orthanc.json",
        #     "exe-storage-folder": "/home/alain/o/build/configs/OrthancStorageRelease",
        # },
        # "local-sqlite-1.13.0-release": {
        #     "orthanc-url": "http://localhost:8046",
        #     "results": results_root_path + "local-sqlite-mainline-release.txt",
        #     "type": "SQLite",
        #     "exe": "/home/alain/Releases/Orthanc-local-release-1.13.0",
        #     "exe-config-file": "/home/alain/o/build/configs/orthanc.json",
        #     "exe-storage-folder": "/home/alain/o/build/configs/OrthancStorageRelease",
        # },
        # "local-sqlite-mainline-with-ordering-release": {
        #     "orthanc-url": "http://localhost:8046",
        #     "results": results_root_path + "local-sqlite-with-release.txt",
        #     "type": "SQLite",
        #     "exe": "/home/alain/Releases/Orthanc-local-release-build-with-ordering-and-analyze-after-50",
        #     "exe-config-file": "/home/alain/o/build/configs/orthanc.json",
        #     "exe-storage-folder": "/home/alain/o/build/configs/OrthancStorageRelease",
        # },
        # "local-sqlite-mainline-without-ordering-release": {
        #     "orthanc-url": "http://localhost:8046",
        #     "results": results_root_path + "local-sqlite-without-release.txt",
        #     "type": "SQLite",
        #     "exe": "/home/alain/Releases/Orthanc-local-release-build-without-ordering-and-analyze-after-50",
        #     "exe-config-file": "/home/alain/o/build/configs/orthanc.json",
        #     "exe-storage-folder": "/home/alain/o/build/configs/OrthancStorageRelease",
        # },
        # "local-pg-10.3-release": {
        #     "orthanc-url": "http://localhost:8046",
        #     "results": results_root_path + "local-pg-10.3-release.txt",
        #     "type": "PG",
        #     "exe": "/home/alain/Releases/Orthanc-local-release-build-without-ordering-and-analyze-after-50",
        #     "exe-config-file": "/home/alain/o/build/configs/orthanc-pg-release-10.3.json",
        #     "exe-storage-folder": "/home/alain/o/build/configs/OrthancStorageRelease",
        #     "db-container": "pg-ref-db"
        # },
        # "local-pg-mainline-with-ordering-release": {
        #     "orthanc-url": "http://localhost:8046",
        #     "results": results_root_path + "local-pg-with-release.txt",
        #     "type": "PG",
        #     "exe": "/home/alain/Releases/Orthanc-local-release-build-without-ordering-and-analyze-after-50",
        #     "exe-config-file": "/home/alain/o/build/configs/orthanc-pg-release-with.json",
        #     "exe-storage-folder": "/home/alain/o/build/configs/OrthancStorageRelease",
        #     "db-container": "pg-ref-db"
        # },
        # "local-pg-mainline-without-ordering-release": {
        #     "orthanc-url": "http://localhost:8046",
        #     "results": results_root_path + "local-pg-without-release.txt",
        #     "type": "PG",
        #     "exe": "/home/alain/Releases/Orthanc-local-release-build-without-ordering-and-analyze-after-50",
        #     "exe-config-file": "/home/alain/o/build/configs/orthanc-pg-release-without.json",
        #     "exe-storage-folder": "/home/alain/o/build/configs/OrthancStorageRelease",
        #     "db-container": "pg-ref-db"
        # },
        # "local-pg-ref": {
        #     "orthanc-url": "http://localhost:8145",
        #     "results": results_root_path + "local-pg-ref.txt",
        #     "type": "PG",
        #     "container": "orthanc-pg-ref",
        #     "db-container": "pg-ref-db"
        # },
        # "local-pg-next": {
        #     "orthanc-url": "http://localhost:8146",
        #     "results": results_root_path + "local-pg-next.txt",
        #     "type": "PG",
        #     "container": "orthanc-pg-next",
        #     "db-container": "pg-next-db"
        # }
    }
else:
    results_root_path = "/results/"

    test_configs = {
        "sqlite-ref": {
            "orthanc-url": "http://orthanc-sqlite-ref:8042",
            "results": results_root_path + "sqlite-ref.txt",
            "type": "SQLite",
            "container": "orthanc-sqlite-ref",
            "db-volume": "orthanc-storage-sqlite-ref"
        },
        # "sqlite-next": {
        #     "orthanc-url": "http://orthanc-sqlite-next:8042",
        #     "results": results_root_path + "sqlite-next.txt",
        #     "type": "SQLite",
        #     "container": "orthanc-sqlite-next",
        #     "db-volume": "orthanc-storage-sqlite-next"
        # },
        "pg-ref": {
            "orthanc-url": "http://orthanc-pg-ref:8042",
            "results": results_root_path + "pg-ref.txt",
            "type": "PG",
            "db-container": "pg-ref-db"
        },
        # "pg-next": {
        #     "orthanc-url": "http://orthanc-pg-next:8042",
        #     "results": results_root_path + "pg-next.txt",
        #     "type": "PG",
        #     "db-container": "pg-next-db"
        # },
    }

def is_local_exe(test_config):
    if "exe" in test_config and "container" in test_config:
        raise RuntimeError("Can not have 'exe' and 'container' defined in test_config " + json.dumps(test_config))

    if "exe" in test_config and (not "exe-config-file" in test_config or not "exe-storage-folder" in test_config):
        raise RuntimeError("Invalid 'exe' config in test_config " + json.dumps(test_config))

    return "exe" in test_config


def upload_instances_worker(o: OrthancApiClient, thread_id: str):
    logging.info(f"Starting uploader thread {thread_id}")
    while True:
        dicom = instances_queue.get()
        if dicom is None:  # stop message
            instances_queue.task_done()
            break        
    
        o.upload(buffer=dicom)
        instances_queue.task_done()

    logging.info(f"Exiting uploader thread {thread_id}")

def save_db_snapshot(test_config, snapshot_size):
    if test_config["type"] == "SQLite":
        result = subprocess.run([
            "docker", "compose", "down", test_config['container']
        ], cwd=here / '..')

        result = subprocess.run([
            "docker", "run", "--rm", 
            "-v", f"databases-benchmark_{test_config['db-volume']}:/volume",
            "-v", f"{here / '../db-snapshots/'}:/db-snapshots",
            "alpine",
            # "zip", "/db-snapshots/sqlite-{snapshot_size}.zip", "/volume/index"
            "cp",  "/volume/index", f"/db-snapshots/sqlite-{snapshot_size}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env)

        print(result.stdout)
        print(result.stderr)

        with zipfile.ZipFile(here / f"../db-snapshots/sqlite-{snapshot_size}.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(here / f"../db-snapshots/sqlite-{snapshot_size}", arcname=f"sqlite-{snapshot_size}")

        os.remove(here / f"../db-snapshots/sqlite-{snapshot_size}")

        result = subprocess.run([
            "docker", "compose", "up", "-d", test_config['container']
        ], cwd=here / '..')
    elif test_config["type"] == "PG":
        result = subprocess.run([
            "docker", "compose", "exec", test_config["db-container"],
            "bash", "-c", f"pg_dump --username=postgres --dbname=postgres --host=localhost --port=5432 -Fc | gzip > /db-snapshots/pg-18-{snapshot_size}.tar.gz"
        ])


def restore_db_snapshot(test_config, snapshot_size):
    if not is_local_exe(test_config):
        result = subprocess.run([
            "docker", "compose", "down", test_config['container']
        ], cwd=here / '..')

    if test_config["type"] == "SQLite":

        snapshot_zip_path=f"{here / '../db-snapshots/sqlite-'}{snapshot_size}.zip"
        if not os.path.exists(snapshot_zip_path):
            urlretrieve(f"https://public-files.orthanc.team/databases-benchmark/sqlite-{snapshot_size}.zip", snapshot_zip_path)

        with zipfile.ZipFile(snapshot_zip_path, 'r') as zip_ref:
            file_name_in_zip = zip_ref.namelist()[0]
            with tempfile.TemporaryDirectory() as tmp_dir_path:
                zip_ref.extractall(tmp_dir_path)
                os.rename(os.path.join(tmp_dir_path, file_name_in_zip), here / f'../db-snapshots/sqlite-{snapshot_size}')

        if is_local_exe(test_config):
            shutil.rmtree(test_config['exe-storage-folder'], ignore_errors=True)
            os.makedirs(test_config['exe-storage-folder'], exist_ok=True)
            # with zipfile(snapshot_zip_path, 'r') as zip_ref:
            #     file_name_in_zip = zip_ref.namelist()[0]
            #     with tempfile.TemporaryDirectory as tmp_dir_path:
            #         zip_ref.extractall(tmp_dir_path)
            #         os.rename(os.path.join(tmp_dir_path, file_name_in_zip), os.path.join(test_config['exe-storage-folder'], "index"))
            # shutil.copy(f"{here / '../db-snapshots/sqlite-'}{snapshot_size}", os.path.join(test_config['exe-storage-folder'], "index"))
            os.rename(f"{here / '../db-snapshots/sqlite-'}{snapshot_size}", os.path.join(test_config['exe-storage-folder'], "index"))
        else:

            result = subprocess.run([
                "docker", "run", "--rm", 
                "-v", f"databases-benchmark_{test_config['db-volume']}:/volume",
                "-v", f"{here / '../db-snapshots/'}:/db-snapshots",
                "alpine",
                "sh", "-c", f"rm -rf /volume/* && mv /db-snapshots/sqlite-{snapshot_size} /volume/index && chown 999:999 /volume/index && chmod 644 /volume/index && ls -al /volume/"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env)

            print(result.stdout)
            print(result.stderr)

    elif test_config["type"] == "PG":
        # restart PG to release all connections
        result = subprocess.run([
            "docker", "compose", "restart", test_config['db-container']
        ], cwd=here / '..')

        # Wait for PostgreSQL to be ready
        subprocess.run([
            "docker", "compose", "exec", test_config["db-container"],
            "bash", "-c",
            "until pg_isready --username=postgres; do sleep 1; done"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

        snapshot_zip_path=f"{here / '../db-snapshots/pg-18-'}{snapshot_size}.tar.gz"
        if not os.path.exists(snapshot_zip_path):
            urlretrieve(f"https://public-files.orthanc.team/databases-benchmark/pg-18-{snapshot_size}.tar.gz", snapshot_zip_path)

        result = subprocess.run([
            "docker", "compose", "exec", test_config["db-container"],
            "bash", "-c", f"dropdb --username=postgres postgres && createdb --username=postgres postgres && gunzip -c /db-snapshots/pg-18-{snapshot_size}.tar.gz | pg_restore --username=postgres --dbname=postgres"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env)

        print(result.stdout)
        print(result.stderr)

    if not is_local_exe(test_config):
        result = subprocess.run([
            "docker", "compose", "up", "-d", test_config['container']
        ], cwd=here / '..')



if generate_snapshots:
    for test_config_name in test_configs:
        test_config = test_configs[test_config_name]

        o = OrthancApiClient(test_config["orthanc-url"])
        o.wait_started()

        stats_before = o.get_statistics()
        studies_count_before = stats_before.studies_count;
        patients_count_before = stats_before.patients_count;
        instances_count_before = stats_before.instances_count;

        i_study = 0
        populator = OrthancTestDbPopulator(o, 1, random_seed=studies_count_before)

        for snapshot_size in snapshots_sizes:
            while o.get_statistics().instances_count < snapshot_size:

                upload_instances_count = 0
                while upload_instances_count < instances_per_step:
                    logging.info(f"Generating study {i_study}")
                    study_id = studies_count_before + i_study
                    tags = populator.generate_patient_tags({})
                    tags["PatientID"] = str(study_id)
                    tags = populator.generate_study_tags(tags, study_id)
                    tags["StudyInstanceUID"] = f"1.{study_id}"
            
                    for i_series in range(0, series_per_studies):
                        tags = populator.generate_series_tags(tags, i_series, study_id)
                        for i_instance in range(0, int(instances_per_step/int(studies_per_step * series_per_studies))):
                            tags = populator.generate_instance_tags(tags, i_instance, i_series, study_id)
                            dicom = helpers.generate_test_dicom_file(width=2, height=2, tags=tags)
                            instances_queue.put(dicom)
                            upload_instances_count += 1
                    i_study += 1
                
                logging.info(f"{test_config_name}: Uploading")

                uploader_threads = []
                for thread_id in range(0, uploader_threads_count):
                    uploader_threads.append(threading.Thread(
                                            target=upload_instances_worker,
                                            name=f"Worker Thread {thread_id}",
                                            args=(o, thread_id, )
                                            ))

                for thread_id in range(0, uploader_threads_count):
                    instances_queue.put(None)  # exit message

                start_upload = time.perf_counter()
                start_upload_orthanc_time = o.get_binary("/tools/now").decode('utf-8')
                last_change_id_before_upload = o.get_json("/changes?last")["Last"]

                for ut in uploader_threads:
                    ut.start()      

                for ut in uploader_threads:
                    ut.join()      

                    end_upload = time.perf_counter()
                logging.info(f"{test_config_name}: Uploading - done in {(end_upload - start_upload):.3f} s")

            save_db_snapshot(test_config, snapshot_size)


results_headers = ["#instances"]
results_y_axis_titles = ["NA"]

measure_upload_time = True
measure_upload_time_with_metadata_caching = False  #note, check the docker-compose file and make sure the "DicomWeb.EnableMetadataCache" is configured with the same value !
measure_tools_find_at_study_on_study_date = True
measure_tools_find_at_study_level_on_patient_name_wildcard_case_insensitive = True
measure_tools_find_at_study_level_on_patient_name_wildcard_case_sensitive = True
measure_wado_rs_single_frame = True
measure_list_series_instances = True
measure_update_attachment_custom_data = True
measure_attachments_info = True
measure_instances = True

if measure_upload_time:
    results_headers.append(f"Upload {instances_per_step} instances [s]")
    results_y_axis_titles.append("[s]")

if measure_upload_time_with_metadata_caching:
    results_headers.append(f"Upload {instances_per_step} instances + compute /metadata [s]")
    results_y_axis_titles.append("[s]")

if measure_tools_find_at_study_on_study_date:
    results_headers.append("5x tools/find at study level on StudyDate (case-sensitive) [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_tools_find_at_study_level_on_patient_name_wildcard_case_insensitive:
    results_headers.append("5x tools/find at study level on PatientName (wildcard - case sensitive=false) [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_tools_find_at_study_level_on_patient_name_wildcard_case_sensitive:
    results_headers.append("5x tools/find at study level on PatientName (wildcard - case sensitive=true) [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_wado_rs_single_frame:
    results_headers.append("5x WADO-RS a single instance [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_list_series_instances:
    results_headers.append("20x /tools/lookup [ms]")    
    results_y_axis_titles.append("[ms]")

    results_headers.append("20x /series/../instances?expand=true [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_update_attachment_custom_data:
    results_headers.append("100x /instances/../update-custom-data [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_instances:
    results_headers.append("1000x /instances/.. [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_attachments_info:
    results_headers.append("1000x /instances/../attachments/dicom/info [ms]")    
    results_y_axis_titles.append("[ms]")



# each step generates 5 studies of 2000 instances
def step(test_config):
    o = OrthancApiClient(test_configs[test_config]["orthanc-url"])
    o.wait_started()

    stats_before = o.get_statistics()
    studies_count_before = stats_before.studies_count;
    patients_count_before = stats_before.patients_count;
    instances_count_before = stats_before.instances_count;

    logging.info(f"{test_config}: Starting step, #patients: {patients_count_before}, #studies: {studies_count_before}, #instances: {instances_count_before} ")

    study_dates = []
    patient_names = []
    dicom_web_instances_uri = []
    series_dicom_ids = []
    upload_instances_count = 0
    last_series_dicom_id = None

    # generate the test images
    for i_study in range(0, studies_per_step):
        logging.info(f"Generating study {i_study}")
        populator = OrthancTestDbPopulator(o, 1, random_seed=studies_count_before)
        study_id = studies_count_before + i_study
        tags = populator.generate_patient_tags({})
        tags["PatientID"] = str(study_id)
        tags = populator.generate_study_tags(tags, study_id)
        tags["StudyInstanceUID"] = f"1.{study_id}"
        
        for i_series in range(0, series_per_studies):
            tags = populator.generate_series_tags(tags, i_series, study_id)
            series_dicom_ids.append(tags["SeriesInstanceUID"])
            for i_instance in range(0, int(instances_per_step/int(studies_per_step * series_per_studies))):
                tags = populator.generate_instance_tags(tags, i_instance, i_series, study_id)
                dicom = helpers.generate_test_dicom_file(width=2, height=2, tags=tags)
                instances_queue.put(dicom)
                upload_instances_count += 1
            
        study_dates.append(tags["StudyDate"])
        patient_names.append(tags["PatientName"])
        dicom_web_instances_uri.append(f"/dicom-web/studies/{tags['StudyInstanceUID']}/series/{tags['SeriesInstanceUID']}/instances/{tags['SOPInstanceUID']}")
        last_series_dicom_id = tags['SeriesInstanceUID']
          
    logging.info(f"{test_config}: Uploading")

    uploader_threads = []
    for thread_id in range(0, uploader_threads_count):
        uploader_threads.append(threading.Thread(
                                target=upload_instances_worker,
                                name=f"Worker Thread {thread_id}",
                                args=(o, thread_id, )
                                ))

    for thread_id in range(0, uploader_threads_count):
        instances_queue.put(None)  # exit message

    start_upload = time.perf_counter()
    start_upload_orthanc_time = o.get_binary("/tools/now").decode('utf-8')
    last_change_id_before_upload = o.get_json("/changes?last")["Last"]

    for ut in uploader_threads:
        ut.start()      

    for ut in uploader_threads:
        ut.join()      

    end_upload = time.perf_counter()
    logging.info(f"{test_config}: Uploading - done in {(end_upload - start_upload):.3f} s")

    result_row = [f"{instances_count_before + upload_instances_count}"]
    if measure_upload_time:
        result_row.append(f"{(end_upload - start_upload):.3f}")

    if measure_upload_time_with_metadata_caching:
        logging.info(f"{test_config}: Waiting for DICOMWeb /metadata to complete")
        last_series_orthanc_id = o.lookup(last_series_dicom_id)[0]
        while "4301" not in o.get_json(f"/series/{last_series_orthanc_id}/attachments"):
            logging.info(f"{test_config}: Waiting for DICOMWeb /metadata to complete (waiting for attachment) /series/{last_series_orthanc_id}/attachments")
            time.sleep(1.1)
        end_upload_with_metadata = time.perf_counter()
        logging.info(f"{test_config}: Waiting for DICOMWeb /metadata - upload + metadata done in {(end_upload_with_metadata - start_upload):.3f} s")

        result_row.append(f"{(end_upload_with_metadata - start_upload):.3f}")

    time.sleep(3)

    if measure_tools_find_at_study_on_study_date:
        start_tools_find = time.perf_counter()
        for study_date in study_dates:
            o.studies.find(case_sensitive=True, query={"StudyDate": study_date})
        end_tools_find = time.perf_counter()
        logging.info(f"{test_config}: 5x tools/find at study level on StudyDate (case sensitive) - done in {(end_tools_find - start_tools_find)*1e3:.3f} ms")

        result_row.append(f"{(end_tools_find - start_tools_find)*1e3:.3f}")

    if measure_tools_find_at_study_level_on_patient_name_wildcard_case_insensitive:
        start_tools_find = time.perf_counter()
        for patient_name in patient_names:
            o.studies.find(case_sensitive=False, query={"PatientName": f"*{patient_name[1:-1].lower()}*"})
        end_tools_find = time.perf_counter()
        logging.info(f"{test_config}: 5x tools/find at study level on PatientName (wildcard - case sensitive=false)- done in {(end_tools_find - start_tools_find)*1e3:.3f} ms")

        result_row.append(f"{(end_tools_find - start_tools_find)*1e3:.3f}")

    if measure_tools_find_at_study_level_on_patient_name_wildcard_case_sensitive:
        start_tools_find = time.perf_counter()
        for patient_name in patient_names:
            o.studies.find(case_sensitive=True, query={"PatientName": f"*{patient_name[1:-1].lower()}*"})
        end_tools_find = time.perf_counter()
        logging.info(f"{test_config}: 5x tools/find at study level on PatientName (wildcard - case sensitive=true)- done in {(end_tools_find - start_tools_find)*1e3:.3f} ms")

        result_row.append(f"{(end_tools_find - start_tools_find)*1e3:.3f}")

    if measure_wado_rs_single_frame:
        start_wado_rs = time.perf_counter()
        for uri in dicom_web_instances_uri:
            o.get_binary(endpoint=uri)
        end_wado_rs = time.perf_counter()
        logging.info(f"{test_config}: 5x DICOMWeb WADO-RS at instance level - done in {(end_wado_rs - start_wado_rs)*1e3:.3f} ms")

        result_row.append(f"{(end_wado_rs - start_wado_rs)*1e3:.3f}")

    if measure_list_series_instances:
        start_lookup = time.perf_counter()
        series_ids = []
        for series_dicom_id in series_dicom_ids:
            series_ids.append(o.lookup(series_dicom_id)[0])
        end_lookup = time.perf_counter()
        logging.info(f"{test_config}: 20x /tools/lookup - done in {(end_lookup - start_lookup)*1e3:.3f} ms")

        start_list_series_instances = time.perf_counter()
        for series_id in series_ids:
            o.get_json(f"/series/{series_id}/instances?expand=true")
        end_list_series_instances = time.perf_counter()
        logging.info(f"{test_config}: 20x /series/../instances?expand=true - done in {(end_list_series_instances - start_list_series_instances)*1e3:.3f} ms")

        result_row.append(f"{(end_lookup - start_lookup)*1e3:.3f}")
        result_row.append(f"{(end_list_series_instances - start_list_series_instances)*1e3:.3f}")

    if measure_update_attachment_custom_data:
        instances_ids = o.post("/tools/find", json={
            "Level": "Instance",
            "Expand": False,
            "Query": {},
            "OrderBy": [{
                "Type": "Metadata",
                "Key": "LastUpdate",
                "Direction": "DESC"
            }],
            "Limit": 100
        }).json()
        start_update_cd = time.perf_counter()
        for instance_id in instances_ids:
            o.post(f"/instances/{instance_id}/update-custom-data", json={})
        end_update_cd = time.perf_counter()
        logging.info(f"{test_config}: 100x /instances/../update-custom-data - done in {(end_update_cd - start_update_cd)*1e3:.3f} ms")

        result_row.append(f"{(end_update_cd - start_update_cd)*1e3:.3f}")

    if measure_instances:
        instances_ids = o.post("/tools/find", json={
            "Level": "Instance",
            "Expand": False,
            "Query": {},
            "OrderBy": [{
                "Type": "Metadata",
                "Key": "LastUpdate",
                "Direction": "DESC"
            }],
            "Limit": 1000
        }).json()
        start_perf = time.perf_counter()
        for instance_id in instances_ids:
            o.get(f"/instances/{instance_id}", json={})
        end_perf = time.perf_counter()
        logging.info(f"{test_config}: 1000x /instances/.. - done in {(end_perf - start_perf)*1e3:.3f} ms")

        result_row.append(f"{(end_perf - start_perf)*1e3:.3f}")

    if measure_attachments_info:
        instances_ids = o.post("/tools/find", json={
            "Level": "Instance",
            "Expand": False,
            "Query": {},
            "OrderBy": [{
                "Type": "Metadata",
                "Key": "LastUpdate",
                "Direction": "DESC"
            }],
            "Limit": 1000
        }).json()
        start_perf = time.perf_counter()
        for instance_id in instances_ids:
            o.get(f"/instances/{instance_id}/attachments/dicom/info", json={})
        end_perf = time.perf_counter()
        logging.info(f"{test_config}: 1000x /instances/../attachments/dicom/info - done in {(end_perf - start_perf)*1e3:.3f} ms")

        result_row.append(f"{(end_perf - start_perf)*1e3:.3f}")


    # write to csv
    results_path = test_configs[test_config]["results"]
    results_file_already_exists = os.path.isfile(results_path)
    
    with open(results_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not results_file_already_exists:
            writer.writerow(results_headers)

        writer.writerow(result_row)

if use_snapshots:
    steps = snapshots_sizes
else:
    steps_count = int(os.environ.get('STEPS_COUNT', '100'))
    steps = [s * instances_per_step for s in range(0, steps_count)]

if local_tests:
    # start the docker-compose (at least for db servers containers ...) and clear the volumes first
    result = subprocess.run([
        "docker", "compose", "down", "-v"
        ], cwd=here / '..')

    result = subprocess.run([
        "docker", "compose", "up", "-d"
        ], cwd=here / '..')


for step_size in steps:
    for test_config_name in test_configs:
        test_config = test_configs[test_config_name]
        if use_snapshots: # restore the snapshot before running the step
            restore_db_snapshot(test_config, step_size)

        if is_local_exe(test_config):
            # start the local Orthanc
            process = subprocess.Popen([test_config['exe'], test_config['exe-config-file']],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)
            concatenated_output = []
            while True:
                line = process.stderr.readline()
                concatenated_output.append(line)
                if line and "Orthanc has stopped" in line:
                    for line in concatenated_output:
                        print("STDERR:", line, end='')
                    raise RuntimeError("Failed to start Orthanc")
                elif line and "Orthanc has started" in line:
                    print("Orthanc has started")
                    break

        step(test_config_name)

        if is_local_exe(test_config):
            process.terminate()
            process.wait()

    if bool(os.environ.get('GENERATE_PLOT', 'True')):

        dfs = []
        plot_prefix_titles = []
        for test_config_name in test_configs:

            dfs.append(pd.read_csv(test_configs[test_config_name]['results']))
            plot_prefix_titles.append(test_config_name)
        
        plt.figure(figsize=(12, 4*(len(results_headers)-1)))

        plot_counter = 1
        for r in range(1, len(results_headers)):
            result = results_headers[r]
            plt.subplot(len(results_headers)-1, 1, plot_counter)

            for i_config in range(0, len(test_configs)):
                plt.plot(dfs[i_config].iloc[:, 0], dfs[i_config].iloc[:, plot_counter], label=f"{plot_prefix_titles[i_config]} - {result}")
            plt.xlabel("# instances in DB")
            plt.ylabel(results_y_axis_titles[r])
            plt.ylim(bottom=0)
            plt.title(result)
            plt.legend()
            plt.grid(True)

            plot_counter+= 1

        plt.tight_layout()

        # Save the plot
        plot_path = results_root_path + "combined_plots.png"
        plt.savefig(plot_path, format='png', dpi=200, bbox_inches='tight')
        plt.close()

