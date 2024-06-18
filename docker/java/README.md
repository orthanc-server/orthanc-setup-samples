# Purpose

This is a sample setup to demonstrate how to deploy an Orthanc Java plugin.

# Description

This demo contains:

- an Orthanc container with the [Java plugin](https://book.orthanc-server.com/plugins/java.html)
  enabled.

Note that the [orthancteam/orthanc](https://orthanc.uclouvain.be/book/users/docker-orthancteam.html) Docker image
contains the Java plugin and the Java SDK only in the `full` version.

# Starting the setup

To start the setup, type: `docker-compose up -d --build` and `docker-compose logs` to access the logs later on.
This will build a very simple Java plugin that implements a simple Rest API endpoint.

# demo

Open [http://localhost:8042/java](http://localhost:8042/java) to get the output from your Java plugin.
