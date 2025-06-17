# Purpose

This is a sample setup to demonstrate how to run orthanc with the advanced storage plugin.

# Description

This demo contains:

- 2 Orthanc containers with the Advanced Storage plugin enabled; both connected to the same DB
- a Postgresql container to store the Orthanc database

# Starting the setup

To start the setup, type: `docker compose up`

# demo

- Orthanc-1 is accessible at [http://localhost:8044/ui/app/](http://localhost:8044/ui/app/)
- Orthanc-2 is accessible at [http://localhost:8045/ui/app/](http://localhost:8045/ui/app/)

You may then copy DICOM files in the `folder-to-index` and see them appear in Orthanc UI.

You may also ingest DICOM files through Orthanc UI and analyze their customized storage path in the docker volume.



