This is a sample setup to demonstrate how you can filter out some instances when
a C-Move is performed.
The instances are filtered based on the SOPClass.

# Description

This demo contains:

- an Orthanc container `orthanc` acting as a PACS.  This container has a custom python plugin
  to handle the C-Move queries and filter out the instances based on the defined filter.
- another Orthanc container `modality` acting as a modality that is querying studies from the PACS.


# Running the demo

First start Orthanc with this command:

```
docker compose pull
docker compose up -d --force-recreate
```

The test scenario will:
- clean both Orthanc instances
# TODO