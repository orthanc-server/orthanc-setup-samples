# Purpose

This is a sample setup to demonstrate how to run an Orthanc in Google Cloud and persist the data inside a PostgreSQL Cloud SQL Instance and a Google Cloud Storage bucket.
Note that you need to have access to osimis/orthanc-pro Docker images in order to run this sample.
Access is restricted to companies who have subscribed a [support contract](https://www.osimis.io/en/services.html).

# Prerequisites

## Cloud SQL Instance

- Create a new PostgreSQL Instance in the Google Cloud Console (i.e: your-orthanc-test-sql).
- copy the postgres user pwd into the file `sql-password.txt`
- In the `network` section, make sure the VM running Orthanc will have access.
- Create an empty `orthanc` database
- Update the environment variables in the docker-compose.yml with SQL Instance IP address

## Cloud Storage

- Create a new storage bucket in the Google Cloud Console (i.e: your-orthanc-test-bucket)
- create a new JSON [https://cloud.google.com/docs/authentication/getting-started](Service Account) for your application.
- make sure that this service account will have access to your bucket
- download the JSON file and save it in service-account.json in this project folder
- Update the environment variables in the docker-compose.yml with the BucketName

# Starting the setup

To start the setup, type: `docker-compose up -d` and `docker-compose logs` to access the logs later on.

# demo

Orthanc is accessible on [http://localhost:8042](http://localhost:8042).  If you upload data to Orthanc,
everything will be stored in the Google cloud.
