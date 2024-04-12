# Purpose

This is a sample setup to demonstrate how to run Orthanc with an AWS S3 storage that is simulated by [minio](https://min.io/).



# Starting the setup

To start the setup, type: `docker-compose up --build -d` and `docker-compose logs` to access the logs later on.

A minio container is started to simulate s3 and an `my-sample-bucket` bucket is created at startup.

# demo

Orthanc is accessible on [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/).  If you upload data to Orthanc,
everything will be stored in the minio storage.
