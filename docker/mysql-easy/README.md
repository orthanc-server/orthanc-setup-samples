# Purpose

This is a sample setup to demonstrate how to configure Orthanc with a
MySQL database for its index the easy way.

# Description

This demo contains:

- an Orthanc container with the [MySQL
  plugin](http://book.orthanc-server.com/plugins/mysql.html)
enabled.
- a MySQL container that will store the Orthanc Index DB (the dicom
  files are stored in a Docker volume)

By using MySQL default DB name and username, the only thing you need
to configure in the MySQL container is the MYSQL_ALLOW_EMPTY_PASSWORD
option.  Check the documentation of the [MySQL Docker image](https://hub.docker.com/_/mysql/) to get more
info about its configuration.

# Starting the setup

To start the setup, type: `docker-compose up -d` and `docker-compose logs` to access the logs later on.

# demo

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 80 on the Docker host (try
[http://localhost](http://localhost)), and Orthanc's DICOM server is
reachable via port 104 on the Docker host.
