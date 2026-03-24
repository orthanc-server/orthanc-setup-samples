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
uv run test-scenario.py
```

The test scenario:
- starts the `docker-compose` setup
- performs some functional REST Api tests
- uploads a test study on 2 Orthanc instances:
  - one with the standard S3 plugin (`s3-default`)
  - one with the S3-Zip python plugin (`s3-zip`)
- cleanup the S3-Zip plugin local storage
- restarts the system to clear the storage caches
- download the studies again

TODO/To discuss:
- series deletions (delete local files + delete zip files in S3 (on DELETED_SERIES event ?)).  This should not be required since we want to keep both the source and the anonymized studies
- more error handling
- handle Orthanc stopped before the zip is moved to S3 and the temporary storage is lost -> remove the resource from Orthanc SQL DB ?
- use the s3 multipart upload (or transfer mode)

Done:
- use a queue to perform `move_series_to_s3` asynchronously
- remove series from `LocalToS3ZipManager`
- add a flag to disable compression in the zip algo ?
- handle max size for the local temporary storage
- added an API route to know where the series is `/series/.../s3-zip/status`
- added an API route to schedule the copy to s3 before the StableSeries event `/series/.../s3-zip/copy-to-s3`
- added an API route override to download the zip directly from s3 through Orthanc `/series/.../archive`

