# Purpose

This is a sample setup to demonstrate how to configure a basic Orthanc
server.

# Description

This demo contains:

- a single basic Orthanc container

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 8042 on the Docker host (try
[http://localhost:8042/](http://localhost:8042/)), and Orthanc's DICOM server is
reachable via port 4242 on the Docker host.
Login/Pwd to connect to the demo: demo/demo
