# Purpose

This is a sample setup to demonstrate how to remove [dicom-as-json files](https://orthanc.uclouvain.be/book/faq/features.html#dicom-as-json-attachments) 
from previous Orthanc versions.

# Description

This demo contains:

- 3 Orthanc containers connected to a PG server.  Only one of the servers can run at any time:
  - `orthanc-19` is an old Orthanc version that still generates dicom-as-json files
  - `orthanc-22` is running Orthanc with the PostgreSQL plugin v5.0 (`orthancteam/orthanc:22.3.0`)
  - `orthanc-24` is running Orthanc with the PostgreSQL plugin v6.2 (`orthancteam/orthanc:24.7.2`)
- a PG server
- a `dicom-as-json-remover` python service

# demo

- start the old `orthanc-19` by running `docker compose up orthanc-19`
- upload files through the UI at http://localhost:8042
- stop it with `Ctrl-C` or `docker compose down orthanc-19`
- to run the demo with `orthanc-22`:
  - start the newer `orthanc-22` by running `docker compose up orthanc-22`
  - build the `dicom-as-json-remover` image by running `docker compose build dicom-as-json-remover`
  - run the `dicom-as-json-remover` image by running `docker compose run dicom-as-json-remover`
- to run the demo with `orthanc-24`:
  - start the newer `orthanc-24` by running `docker compose up orthanc-24`
  - adapt the `docker-compose.yml` file for `orthanc-24` (check comments in the file)
  - build the `dicom-as-json-remover` image by running `docker compose build dicom-as-json-remover`
  - run the `dicom-as-json-remover` image by running `docker compose run dicom-as-json-remover`
- the `dicom-as-json` files shall have been removed from the storage.  Note that the python script
  will not remove empty folders like Orthanc does.
