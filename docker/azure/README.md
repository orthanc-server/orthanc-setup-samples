# Purpose

This is a sample setup to demonstrate how to run an Orthanc in Azure and persist the data inside an Azure SQL database and Blob Storage.
Note that you need to have access to osimis/orthanc-pro Docker images and an MSSQL license string in order to run this sample.
Access is restricted to companies who have subscribed a [support contract](https://www.osimis.io/en/services.html).
Please also note that on SELinux enabled systems, you need to run Docker 17.03.3-ce or later so that the secrets path is relabelled to avoid a Permission Denied which causes the plugin not to load and Orthanc to stop.

# Prerequisites

## Blob storage

- Create a blob storage in the Azure Console (i.e: yourblobstorage).
- No need to create a container, Orthanc will create it.
- In the `Firewall and virtual networks` section, make sure the VM running Orthanc will have access.
- Copy the ConnectionString (from the Access Keys menu).  The connection string looks like `DefaultEndpointsProtocol=https;AccountName=yourblobstorage;AccountKey=yyy==;EndpointSuffix=core.windows.net`.
  You should copy it in `blob-connection-string.txt`

## Azure SQL

- Create a new SQL Database (i.e: yourdb on yourserver)
- In the `Firewall settings` section, make sure the VM running Orthanc will have access.
- Copy the ConnectionString (from the `Connection strings` menu).  The connection strink looks like `Server=tcp:yourserver.database.windows.net,1433;Initial Catalog=yourdb;Persist Security Info=False;User ID=youruser;Password={your_password};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;`.  You should copy it in `mssql-connection-string.txt` after this text: `Driver={ODBC Driver 17 for SQL Server};`
- obtain an MSSQL license string from Osimis


# Starting the setup

To start the setup, type: `docker-compose up -d` and `docker-compose logs` to access the logs later on.

# demo

Orthanc is accessible on [http://localhost:8042](http://localhost:8042).  If you upload data to Orthanc,
everything will be stored in the Azure cloud.
