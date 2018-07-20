# Purpose

This is a sample setup to demonstrate how to configure Orthanc with a
MSSQL database for its index the easy way.

# Description

This demo contains:

- an Orthanc container with the [MSSQL
  plugin](https://osimis.atlassian.net/wiki/spaces/OKB/pages/302743840/MSSQL+Index+plugin)
enabled.
- a MSSQL container that will store the Orthanc Index DB (the dicom
  files are stored in a Docker volume)

By using MSSQL default DB name and username, the only thing you need
to configure in the MSSQL container is the `SA_PASSWORD`
option.  Check the documentation of the [MSSQL Docker image](https://hub.docker.com/r/microsoft/mssql-server-linux/) to get more
info about its configuration.

# Starting the setup

To start the setup, type: `docker-compose up -d` and `docker-compose logs` to access the logs later on.

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 80 on the Docker host (try
[http://localhost](http://localhost)), and Orthanc's DICOM server is
reachable via port 104 on the Docker host.
