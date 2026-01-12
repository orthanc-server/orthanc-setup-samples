import orthanc
from s3_zip_storage_plugin import register_s3_zip_storage_plugin, on_stable_series


# this only the registers the storage area plugin, 
# this does not register the change callback since there are chances that you need to monitor the changes too
register_s3_zip_storage_plugin()

def on_change(changeType, level, resource):
    if changeType == orthanc.ChangeType.STABLE_SERIES:
        on_stable_series(series_id=resource)

orthanc.RegisterOnChangeCallback(on_change)
