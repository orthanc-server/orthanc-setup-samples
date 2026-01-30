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
- series deletions (delete local files + delete zip files in S3 (on DELETED_SERIES event ?)).  This should not be required since we want to keep both the source and the anonymized studies
- more error handling
- handle max size for the local temporary storage
- handle other attachments than DICOM ? (no: there are no other attachments)
- handle Orthanc stopped before the zip is moved to S3 and the temporary storage is lost -> remove the resource from Orthanc SQL DB ?
- add an API route to know where the series is ...
- add a route to trigger the move: SetStableStatus() ?
- override /series/.../archive-s3-zip to return directly the zip from s3
  or, add the s3 path in the series/metadata such that another client can download it directly
- use the s3 multipart upload (or transfer mode)

Done:
- use a queue to perform `move_series_to_s3` asynchronously
- remove series from `LocalToS3ZipManager`
- add a flag to disable compression in the zip algo ?
