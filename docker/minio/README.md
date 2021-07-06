# Purpose

This is a sample setup to demonstrate how to run an Orthanc AWS S3 storage with [minio](https://min.io/).
Note that you need to have access to osimis.azurecr.io/orthanc-pro Docker images in order to run this sample.
Access is restricted to companies who have subscribed a [support contract](https://www.osimis.io/en/services.html).


# Starting the setup

To start the setup, type: `docker-compose up -d` and `docker-compose logs` to access the logs later on.

Before you upload any DICOM file in Orthanc, connect to the [minio interface](http://localhost:9000) and create
a `my-sample-bucket` bucket.  Also make sure to edit the Policy to `Read-Write`.

# demo

Orthanc is accessible on [http://localhost:8042](http://localhost:8042).  If you upload data to Orthanc,
everything will be stored in the minio storage.
