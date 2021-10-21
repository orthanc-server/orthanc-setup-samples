# Purpose

This is a sample setup to demonstrate how to configure Orthanc with a
MSSQL database for its index using the [ODBC plugin](https://book.orthanc-server.com/plugins/odbc.html).
Compared to the other MSSQL demo, this one uses a self-signed certificate on the MSSQL server-side.

# Description

This demo contains:

- an Orthanc container with the ODBC plugin enabled.
- a MSSQL container that will store the Orthanc Index DB (the dicom files are stored in a Docker volume)

The MSSQL container has been customized to create the Orthanc DB at startup.

The Orthanc container has been customized to include the MSODBC drivers that are not installed in the default image.
(check the [Dockerfile](new-orthanc/Dockerfile))

# Starting the setup

To start the setup, type: `docker-compose up --build` to access the logs later on.

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 8042 on the Docker host (try
[http://localhost:8042](http://localhost:8042)), and Orthanc's DICOM server is
reachable via port 104 on the Docker host.




openssl s_client -showcerts -verify 5 -connect dicom-db.database.windows.net:1433
openssl s_client -connect index-mssql:1433

/opt/mssql-tools/bin/sqlcmd -S index-mssql,1433 -U sa -P MyStrOngPa55word!
>1 select name from sys.databases;
>2 go
