import orthanc
import json
import hashlib


class Helpers:

    @classmethod
    # note: this returns a hash that is not necessarily identical to the Orthanc series_id but that has the same "uniqueness" since it is based on the same inputs
    def get_series_hash(cls, dicom_instance: orthanc.DicomInstance) -> str:
        tags = json.loads(dicom_instance.GetInstanceSimplifiedJson())

        combined_id = f"{tags['PatientID']}|{tags['StudyInstanceUID']}|{tags['SeriesInstanceUID']}"
        return hashlib.sha1(combined_id.encode('utf-8')).hexdigest()
        

