# Purpose

This docker-compose file presents various way to configure Orthanc through
environment variables, secrets or configuration files.

More details about the configuration can be found in the [Orthanc book](https://book.orthanc-server.com/users/docker-osimis.html)

# Starting the setup

To start the setup, type: `docker-compose up --build orthanc-file` where `orthanc-file` 
is the name of the service you want to start.  It is advised to start/stop the services one
by one.

Disclaimer: this is not a real setup, all orthancs are connected to the same DB which is not 
an ideal situation.  Check the [Use multiple Orthanc on the same DB](../docker/multiple-orthancs-on-same-db) sample to demonstrate how to connect multiple Orthanc on the same PostgreSQL database and perform HTTP load balancing.
