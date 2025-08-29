This is a sample setup to demonstrate how you can stabilize a study as soon as you receive
a storage commitment request.

# Description

This demo contains:

- an Orthanc container `orthanc` acting as the DICOM Server.  This container has a custom python plugin
  to handle the Storage Commitment SCP and stabilize the study as soon as it has received
  a storage commitment request for ALL instances currently stored in Orthanc.
  A Lua handler is also installed to demonstrate that the STABLE_STUDY event is generated and handled correctly.
- another Orthanc container `modality` acting as a modality that is pushing data and sending the storage commitment request. 


# Running the demo

First start Orthanc with this command:

```
docker compose pull
docker compose up -d --force-recreate
```

Then, launch the test scenario by running:

```
pip install orthanc-api-client
python test.py
```

The test scenario will:
- clean both Orthanc instances, 
- upload 3 files from 3 studies
- show the Stable status of all the studies currently stored in Orthanc -> they should be Unstable
- send the storage commitment request
- show the Stable status of all the studies currently stored in Orthanc -> they should now be Stable

In the logs, you may also check that the Lua script has displayed 3 log messages:

```
LUA OnStableStudy ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2
LUA OnStableStudy 46d287d6-3f7f988f-18eca55f-7078bdf9-028e9a0b
LUA OnStableStudy b9c08539-26f93bde-c81ab0d7-bffaf2cb-a4d0bdd0
```