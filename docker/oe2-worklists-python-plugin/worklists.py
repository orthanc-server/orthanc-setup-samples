import orthanc
import pprint
import json
from datetime import datetime

from orthanc_tools import OldFilesDeleter, DicomWorklistBuilder, OldFilesDeleter

# This plugin adds an API route to generate a worklist file based on the patient information received.
# The accession number will be the datetime (YYYMMDDHHMMSS).
# This plugin relies on the ortanc-tools lib (https://github.com/orthanc-team/python-orthanc-tools) for the worklist building.


# Orthanc Rest API callback
def OnPostWorklist(output, uri, **request):

    if request['method'] != 'POST':
        output.SendMethodNotAllowed('POST')

    study_id = request['groups'][0]

    # get DICOM tags
    study_info = json.loads(orthanc.RestApiGet(f'/studies/{study_id}'))
    first_series_info = json.loads(orthanc.RestApiGet(f'/series/{study_info['Series'][0]}'))
    study_tags = {**study_info['MainDicomTags'], **study_info['PatientMainDicomTags'], **first_series_info['MainDicomTags']}

    # get wl folder path
    wl_folder_path = json.loads(orthanc.GetConfiguration()).get('Worklists').get('Database')

    # build worklist
    builder = DicomWorklistBuilder(wl_folder_path)
    patient_data = {}
    patient_data["PatientName"] = study_tags["PatientName"]
    patient_data["PatientID"] = study_tags["PatientID"]
    patient_data["AccessionNumber"] = datetime.now().strftime("%Y%m%d%H%M%S")
    patient_data["PatientBirthDate"] = study_tags["PatientBirthDate"]
    patient_data["PatientSex"] = study_tags["PatientSex"]
    patient_data["RequestedProcedureID"] = "UNKNOWN"
    patient_data['SpecificCharacterSet'] = "ISO_IR 100"
    patient_data['ScheduledStationAETitle'] = "UNKNOWN"
    patient_data['ScheduledProcedureStepID'] = "UNKNOWN"
    patient_data['Modality'] = study_tags["Modality"]

    result = builder.generate(values = patient_data)

    # Delete old files
    deleter = OldFilesDeleter(wl_folder_path, timeout=24*3600.0)
    deleter.execute_once()

    output.AnswerBuffer('ok\n', 'text/plain')


orthanc.RegisterRestCallback('/studies/(.*)/create-worklist', OnPostWorklist)