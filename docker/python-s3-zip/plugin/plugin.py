import sys

# Failsafe: print directly to stderr before any logging framework is involved.
# If you see this line in container logs but nothing else from s3zip, the
# logging framework itself is misconfigured.
print("[s3zip] plugin.py module is being loaded (standalone entry point)", file=sys.stderr)

import orthanc
from s3_zip_storage_plugin import register_s3_zip_storage_plugin, on_stable_series, on_orthanc_stopped, on_orthanc_started
from s3zip_logging import get_logger

logger = get_logger(__name__)

# this only the registers the storage area plugin,
# this does not register the change callback since there are chances that you need to monitor the changes too
logger.info("S3Zip standalone plugin loading")
register_s3_zip_storage_plugin()

def on_change(changeType, level, resource):
    logger.debug("on_change callback received",
                 change_type=str(changeType),
                 level=str(level),
                 resource=str(resource))
    if changeType == orthanc.ChangeType.STABLE_SERIES:  # TODO: act on stabled anonymized series
        on_stable_series(series_id=resource)
    elif changeType == orthanc.ChangeType.ORTHANC_STARTED:
        on_orthanc_started()
    elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:
        on_orthanc_stopped()

orthanc.RegisterOnChangeCallback(on_change)
logger.info("S3Zip standalone plugin loaded, on_change callback registered")
