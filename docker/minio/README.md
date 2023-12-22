# Purpose

This is a sample setup to demonstrate how to run Orthanc with an AWS S3 storage that is simulated by [minio](https://min.io/).



# Starting the setup

To start the setup, type: `docker-compose up --build -d` and `docker-compose logs` to access the logs later on.

Before you upload any DICOM file in Orthanc, connect to the [minio interface](http://localhost:9000) (`minio/miniopwd`) 
and create a `my-sample-bucket` bucket.  Also make sure to edit the Policy to `Read-Write`.

# demo

Orthanc is accessible on [http://localhost:8042](http://localhost:8042).  If you upload data to Orthanc,
everything will be stored in the minio storage.
