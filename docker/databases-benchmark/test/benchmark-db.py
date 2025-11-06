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


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


local_tests = False

if local_tests:
    results_root_path = "../results/"

    test_configs = {
        "local-8048": {
            "orthanc-url": "http://localhost:8048",
            "results": results_root_path + "local-8048.txt"
        }
    }
else:
    results_root_path = "/results/"

    test_configs = {
        "pg-1.12.4": {
            "orthanc-url": "http://orthanc-pg-old:8042",
            "results": results_root_path + "pg-1.12.4.txt"
        },
        "pg-1.12.9": {
            "orthanc-url": "http://orthanc-pg-129:8042",
            "results": results_root_path + "pg-1.12.9.txt"
        },
#   "sqlite-1.12.1": {
#     "orthanc-url": "http://orthanc-sqlite-121:8042",
#     "results": results_root_path + "sqlite-1.12.1.txt"
#   },
#   "sqlite-1.12.9": {
#     "orthanc-url": "http://orthanc-sqlite-129:8042",
#     "results": results_root_path + "sqlite-1.12.9.txt"
#   },
#   "sqlite-next": {
#     "orthanc-url": "http://orthanc-sqlite-next:8042",
#     "results": results_root_path + "sqlite-next.txt"
#   },
#   "pg-1.12.9": {
#     "orthanc-url": "http://orthanc-pg:8042",
#     "results": results_root_path + "pg-1.12.9.txt"
#   },
#   "mysql": {
#     "orthanc-url": "http://orthanc-mysql:8042",
#     "results": results_root_path + "mysql.txt"
#   }
    }

instances_per_step = int(os.environ.get('INSTANCES_PER_STEP', '5000'))
results_headers = ["#instances"]
results_y_axis_titles = ["NA"]

measure_upload_time = True
measure_upload_time_with_metadata_caching = True
measure_tools_find_at_study_level = True
measure_wado_rs_single_frame = True
measure_list_series_instances = True

if measure_upload_time:
    results_headers.append(f"Upload {instances_per_step} instances [s]")
    results_y_axis_titles.append("[s]")

if measure_upload_time_with_metadata_caching:
    results_headers.append(f"Upload {instances_per_step} instances + compute /metadata [s]")
    results_y_axis_titles.append("[s]")

if measure_tools_find_at_study_level:
    results_headers.append("5x tools/find at study level on StudyDate [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_wado_rs_single_frame:
    results_headers.append("5x WADO-RS a single instance [ms]")    
    results_y_axis_titles.append("[ms]")

if measure_list_series_instances:
    results_headers.append("20x /tools/lookup [ms]")    
    results_y_axis_titles.append("[ms]")

    results_headers.append("20x /series/../instances?expand=true [ms]")    
    results_y_axis_titles.append("[ms]")


uploader_threads_count = os.environ.get("UPLOADER_THREADS_COUNT", 5)
instances_queue = queue.Queue(0)


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
    dicom_web_instances_uri = []
    series_dicom_ids = []
    upload_instances_count = 0
    last_series_dicom_id = None

    # generate the test images
    for i_study in range(0, 5):
        logging.info(f"Generating study {i_study}")
        populator = OrthancTestDbPopulator(o, 1, random_seed=studies_count_before)
        study_id = studies_count_before + i_study
        tags = populator.generate_patient_tags({})
        tags["PatientID"] = str(study_id)
        tags = populator.generate_study_tags(tags, study_id)
        tags["StudyInstanceUID"] = f"1.{study_id}"
        
        for i_series in range(0, 4):
            tags = populator.generate_series_tags(tags, i_series, study_id)
            series_dicom_ids.append(tags["SeriesInstanceUID"])
            for i_instance in range(0, int(instances_per_step/int(4*5))):
                tags = populator.generate_instance_tags(tags, i_instance, i_series, study_id)
                dicom = helpers.generate_test_dicom_file(width=2, height=2, tags=tags)
                instances_queue.put(dicom)
                upload_instances_count += 1
            
        study_dates.append(tags["StudyDate"])
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

    if measure_tools_find_at_study_level:
        start_tools_find = time.perf_counter()
        for study_date in study_dates:
            o.studies.find(query={"StudyDate": study_date})
        end_tools_find = time.perf_counter()
        logging.info(f"{test_config}: 5x tools/find at study level on StudyDate - done in {(end_tools_find - start_tools_find)*1e3:.3f} ms")

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


    # write to csv
    results_path = test_configs[test_config]["results"]
    results_file_already_exists = os.path.isfile(results_path)
    
    with open(results_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not results_file_already_exists:
            writer.writerow(results_headers)

        writer.writerow(result_row)

steps_count = int(os.environ.get('STEPS_COUNT', '10'))

for s in range(0, steps_count):
    for test_config in test_configs:
        step(test_config)

    if bool(os.environ.get('GENERATE_PLOT', 'True')):

        dfs = []
        plot_prefix_titles = []
        for test_config in test_configs:
            dfs.append(pd.read_csv(test_configs[test_config]['results']))
            plot_prefix_titles.append(test_config)
        
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

