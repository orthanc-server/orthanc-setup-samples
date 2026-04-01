import orthanc
import json
import hashlib
from s3zip_logging import get_logger

logger = get_logger(__name__)


class Helpers:

    @classmethod
    # note: this returns a hash that is not necessarily identical to the
    # Orthanc series_id but that has the same "uniqueness" since it is based
    # on the same inputs
    def get_series_hash(cls, dicom_instance: orthanc.DicomInstance) -> str:
        tags = json.loads(dicom_instance.GetInstanceSimplifiedJson())

        patient_id = tags['PatientID']
        study_uid = tags['StudyInstanceUID']
        series_uid = tags['SeriesInstanceUID']

        combined_id = f"{patient_id}|{study_uid}|{series_uid}"
        series_hash = hashlib.sha1(combined_id.encode('utf-8')).hexdigest()

        logger.debug("computed series hash",
                     patient_id=patient_id,
                     study_instance_uid=study_uid,
                     series_instance_uid=series_uid,
                     series_hash=series_hash)

        return series_hash


