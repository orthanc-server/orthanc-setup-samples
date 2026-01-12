# Purpose

This is a sample setup to demonstrate how to implement a custom python storage plugin that
zips series before uploading them into S3.

In the setup, we do introduce an artificial latency between Orthanc and the S3 plugin to
demonstrate how the S3-Zip plugin helps improve upload/download time on a system with a 
large latency.

# Description

To run the setup:

```
docker pull orthancteam/orthanc-pre-release:master-unstable
pip install boto3 orthanc-tools
python test-scenario.py
```

The test scenario:
- starts the `docker-compose` setup
- uploads a test study on 2 Orthanc instances:
  - one with the standard S3 plugin (`s3-default`)
  - one with the S3-Zip python plugin (`s3-zip`)
- cleanup the S3-Zip plugin local storage
- restarts the system to clear the storage caches
- download the studies again

TODO/To discuss:
- series deletions (delete local files + delete zip files in S3 (on DELETED_SERIES event ?))
- more error handling
- remove series from `LocalToS3ZipManager`
- handle max size for the local temporary storage
- use a queue to perform `move_series_to_s3` asynchronously
- handle other attachments than DICOM