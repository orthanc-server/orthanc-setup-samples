# Purpose

This is a sample setup to demonstrate how to run an Orthanc AWS S3 storage with [minio](https://min.io/).
Note that you need to build the S3 plugin since the plugin is not included in the osimis/orthanc images.


# Starting the setup

To start the setup, type: `docker-compose up --build -d` and `docker-compose logs` to access the logs later on.

Before you upload any DICOM file in Orthanc, connect to the [minio interface](http://localhost:9000) and create
a `my-sample-bucket` bucket.  Also make sure to edit the Policy to `Read-Write`.

# demo

Orthanc is accessible on [http://localhost:8042](http://localhost:8042).  If you upload data to Orthanc,
everything will be stored in the minio storage.
