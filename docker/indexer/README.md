# Purpose

This is a sample setup to demonstrate how an Orthanc instance can be used to index and existing folder hierarchy
with dicom-files.


# Description

This demo contains:

- an Orthanc container with the [Orthanc-indexer](https://book.orthanc-server.com/plugins/indexer.html) plugin that is configured to parse
  the folder `dicomFiles` from this repository. 

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Connect to the orthanc simulating the modality on [http://localhost:8042](http://localhost:8042) (login/pwd: demo/demo).
- The dicom files from this repository have been parsed and will appear in the list of studies & patients.
- If you upload a new image in Orthanc, it will be stored in the nominal `OrthancStorage` folder (which is mapped to a docker volume)

