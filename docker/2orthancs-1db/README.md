# Purpose

This is a sample setup to demonstrate how to configure 2 Orthancs with a
single PostgreSQL database. This should allow to improve performances.

# Description

This demo contains:

- an Orthanc container (orthanc-storage) with the [PostgreSQL
  plugin](http://book.orthanc-server.com/plugins/postgresql.html)
enabled.
- a second Orthanc container (orthanc-viewer) with the [PostgreSQL
  plugin](http://book.orthanc-server.com/plugins/postgresql.html)
enabled and the [Viewer plugin](http://book.orthanc-server.com/plugins/webviewer.html) enabled.
- a PostgreSQL container that will store the Orthanc Index DB (the dicom
  files are stored in a Docker volume)

By using PostgreSQL default DB name and username, there is no need to
configure anything in the PostgreSQL container.

First Orthanc should be used for DICOM files exchange.
Second Orthanc should be used for viewer.

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 80 on the Docker host (try
[http://localhost](http://localhost)), and Orthanc's DICOM server is
reachable via port 104 on the Docker host.
