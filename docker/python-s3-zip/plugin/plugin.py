import orthanc
from s3_zip_storage_plugin import register_s3_zip_storage_plugin, on_stable_series, on_orthanc_stopped, on_orthanc_started


# this only the registers the storage area plugin, 
# this does not register the change callback since there are chances that you need to monitor the changes too
register_s3_zip_storage_plugin()

def on_change(changeType, level, resource):
    if changeType == orthanc.ChangeType.STABLE_SERIES:  # TODO: act on stabled anonymized series
        on_stable_series(series_id=resource)
    elif changeType == orthanc.ChangeType.ORTHANC_STARTED:
        on_orthanc_started()
    elif changeType == orthanc.ChangeType.ORTHANC_STOPPED:
        on_orthanc_stopped()

orthanc.RegisterOnChangeCallback(on_change)
