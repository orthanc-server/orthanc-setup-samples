from orthanc_api_client import OrthancApiClient
import requests


o = OrthancApiClient('http://orthanc-for-admin:8042', user='admin', pwd='admin')
#o = OrthancApiClient('http://192.168.0.10:8042', user='admin', pwd='admin')

if not o.wait_started(timeout=20):
    print("could not connect to Orthanc")
    exit(1)

# download a sample image and upload it to Orthanc
sample_file = requests.get(url='https://demo.orthanc-server.com/instances/c9fcb81d-9644e671-54069338-6b3f01bf-1251713a/file').content

original_instance_id = o.upload(buffer=sample_file)[0]
original_study_id = o.instances.get_parent_study_id(orthanc_id=original_instance_id)

# perform cleanup in case we run this script multiple times
studies = o.studies.find(query={
    "InstitutionName": "INST-1\\INST-2"
})

for study in studies:
    o.studies.delete(study.orthanc_id)

# create modified versions of this instance to simulate 5 studies, 4 patients and 2 institutions

o.studies.modify(
    orthanc_id=original_study_id,
    replace_tags={
        "PatientName": "PN-A",
        "PatientID": "1-A",
        "PatientBirthDate": "19900101",
        "PatientSex": "U",
        "InstitutionName": "INST-1",
        "StudyInstanceUID": "1.1",
        "StudyID": "1",
        "StudyDescription": "Study 1",
        "StudyDate": "20210917",
        "SeriesInstanceUID": "1.1.1"
    },
    force=True,
    delete_original=False
)

o.studies.modify(
    orthanc_id=original_study_id,
    replace_tags={
        "PatientName": "PN-A",
        "PatientID": "1-A",
        "PatientBirthDate": "19900101",
        "PatientSex": "U",
        "InstitutionName": "INST-1",
        "StudyInstanceUID": "1.2",
        "StudyID": "2",
        "StudyDescription": "Study 2",
        "StudyDate": "20211204",
        "SeriesInstanceUID": "1.2.1"
    },
    force=True,
    delete_original=False
)

o.studies.modify(
    orthanc_id=original_study_id,
    replace_tags={
        "PatientName": "PN-B",
        "PatientID": "1-B",
        "PatientBirthDate": "19950505",
        "InstitutionName": "INST-1",
        "StudyInstanceUID": "1.3",
        "StudyID": "3",
        "StudyDescription": "Study 3",
        "StudyDate": "20220524",
        "SeriesInstanceUID": "1.3.1"
    },
    force=True,
    delete_original=False
)

o.studies.modify(
    orthanc_id=original_study_id,
    replace_tags={
        "PatientName": "PN-C",
        "PatientID": "2-C",
        "PatientBirthDate": "19990909",
        "InstitutionName": "INST-2",
        "StudyInstanceUID": "1.4",
        "StudyID": "4",
        "StudyDescription": "Study 4",
        "StudyDate": "20220114",
        "SeriesInstanceUID": "1.4.1"
    },
    force=True,
    delete_original=False
)

o.studies.modify(
    orthanc_id=original_study_id,
    replace_tags={
        "PatientName": "PN-D",
        "PatientID": "2-D",
        "PatientBirthDate": "20001231",
        "InstitutionName": "INST-2",
        "StudyInstanceUID": "1.5",
        "StudyID": "5",
        "StudyDescription": "Study 5",
        "StudyDate": "20220204",
        "SeriesInstanceUID": "1.5.1"
    },
    force=True,
    delete_original=False
)

o.studies.delete(original_study_id)