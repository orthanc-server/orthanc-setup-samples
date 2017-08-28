# Purpose

This is a sample setup to demonstrate how to configure a basic Orthanc
server.

# Description

This demo contains:

- a single basic Orthanc container

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 80 on the Docker host (try
[http://localhost/](http://localhost/)), and Orthanc's DICOM server is
reachable via port 104 on the Docker host.
