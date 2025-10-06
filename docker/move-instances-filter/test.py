"""
TODO:
- test a move a study
- test a move a series
- test a move an instance
- test a move of several studies
- test a move of several series
- test a move of several instances
SOPClass to filter:

1.2.840.10008.5.1.4.1.1.104.1

"""

import time
from orthanc_api_client import OrthancApiClient


# wait Orthanc is alive and empty it
modality = OrthancApiClient('http://localhost:8043')
modality.wait_started()
modality.delete_all_content()

pacs = OrthancApiClient('http://localhost:8042')
pacs.wait_started()
pacs.delete_all_content()

target_server = 'orthanc'

print("Both Orthanc instances are alive and empty")

# upload a folder
uploaded_instances_ids = pacs.upload_folder('./samples')

study_uid = pacs.instances.get_tags(uploaded_instances_ids[0]).get('StudyInstanceUID')

modality.modalities.move_study(from_modality="orthanc", dicom_id=study_uid, to_modality_aet="MODALITY")

# TODO: test all cases. Make this file a true test file