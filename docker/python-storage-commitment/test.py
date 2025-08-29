import time
from orthanc_api_client import OrthancApiClient


def show_studies_stability_status(o: OrthancApiClient):
    studies_id = o.studies.get_all_ids()
    for study_id in studies_id:
        study = o.get_json(f"/studies/{study_id}")
        print(f"Stuyd {study_id} stable status is {study['IsStable']}")


# wait Orthanc is alive and empty it
modality = OrthancApiClient('http://localhost:8046')
modality.wait_started()
modality.delete_all_content()

server = OrthancApiClient('http://localhost:8045')
server.wait_started()
server.delete_all_content()

target_server = 'orthanc'

print("Both Orthanc instances are alive and empty")

# upload a folder
uploaded_instances_ids = modality.upload_folder('../../dicomFiles')

# retrieve all instance ids and sop class uids
dicom_instances = []

for instance_id in uploaded_instances_ids:
    instance_tags = modality.instances.get_tags(instance_id)
    dicom_instances.append([
        instance_tags.get('SOPClassUID'),
        instance_tags.get('SOPInstanceUID')
    ])

# send the study from the modality to the server
modality.modalities.store(target_modality=target_server, 
                          resources_ids=uploaded_instances_ids)

print("Stability status before storage commitment")
show_studies_stability_status(server)

# send the storage commitment
transaction = modality.post(f'/modalities/{target_server}/storage-commitment', json={
    'DicomInstances': dicom_instances
}).json()

print("Waiting for the storage commitment request to complete")
# wait for the storage commitment to complete
is_complete = False
while not is_complete:
    time.sleep(0.1)
    s = modality.get_json(f'/storage-commitment/{transaction["ID"]}')
    is_complete = s['Status'] != 'Pending'


print("Stability status after storage commitment")
show_studies_stability_status(server)
