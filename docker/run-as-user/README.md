# Purpose

This is a sample setup to demonstrate how to run the `orthancteam/orthanc` image as a non root user.

# Description

This demo contains:

- an Orthanc container that is being run as the `orthanc` user instead of `root`
- an initialization container that makes sure the volume has the right permissions for the `orthanc` user

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 8042 on the Docker host (try [http://localhost:8042](http://localhost:8042))