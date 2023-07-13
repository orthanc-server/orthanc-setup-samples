# Purpose

This is a sample setup to demonstrate how to export DICOM studies from a PACS to 
a human-friendly organized S3 folder.

# Description

This demo contains:

- An Orthanc instance simulating the PACS
- An Orthanc instance acting as a gateway between the PACS and S3
- a Minio container simulating the S3 storage

# Starting the setup

To start the setup, type: `docker-compose up --build` then, you first need to connect
to the [minio UI](http://localhost:9000) (user: `minio`, pwd: `miniopwd`) to create a `test-bucket` bucket.  
Also make sure to edit the Policy to `Read-Write`.


# demo

- Connect to the Orthanc instance acting as a PACS is accessible on [http://localhost:8043/ui/app/](http://localhost:8043/ui/app/)
- Upload a dicom study in the PACS UI
- Through the UI, `Send` the study to the DICOM destination `gw-to-s3`
- Wait a few seconds
- Open the [minio UI](http://localhost:9000) and browse the `test-bucket` to check your
  study has been exported
- Check the Orthanc instance acting as a Gateway [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/) (user: `demo`, pwd: `demo`)
  and check that the data has been deleted after being transferred

## going further

In a production environment, you should:
- store your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in [Docker secrets](https://docs.docker.com/compose/use-secrets/) and not env var
- adapt the `S3_PATH_TEMPLATE` to your needs.  Any DICOM Tag name can be used in the template.  A `/` will create a "folder" in S3.  Do not forget the `.zip` extension.
- possibly remove the `S3_ENDPOINT` env var that might not be required with a real S3 account.
- increase the Orthanc configuration `"StableAge": 3` to 60 or 300 seconds to allow more time for the gateway to consider that a study is complete before sending it to S3.
- possibly configure `S3_DELETE_AFTER_EXPORT` to `"false"` if you want the data to remain in Orthanc after it has been transferred.  In this case, we recommand to 
  configure Orthanc with a `"MaximumStorageSize"` configuration to limit the amount of data that can be stored in Orthanc.