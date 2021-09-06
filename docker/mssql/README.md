# Purpose

This is a sample setup to demonstrate how to configure Orthanc with a
MSSQL database for its index using the [ODBC plugin](https://book.orthanc-server.com/plugins/odbc.html).

# Description

This demo contains:

- an Orthanc container with the ODBC plugin enabled.  Note that the MSODBC drivers are not installed
  by default in the `osimis/orthanc` images so you must build your own image with a [Dockerfile](new-orthanc/Dockerfile)
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
