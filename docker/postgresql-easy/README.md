# Purpose

This is a sample setup to demonstrate how to configure Orthanc with a
PostgreSQL database for its index the easy way.

# Description

This demo contains:

- an Orthanc container with the [PostgreSQL
  plugin](http://book.orthanc-server.com/plugins/postgresql.html)
enabled.
- a PostgreSQL container that will store the Orthanc Index DB (the dicom
  files are stored in a Docker volume)

By using PostgreSQL default DB name and username, there is no need to
configure anything in the PostgreSQL container.

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 80 on the Docker host (try
[http://localhost](http://localhost)), and Orthanc's DICOM server is
reachable via port 104 on the Docker host.
