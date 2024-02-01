# Purpose

This is a sample setup to demonstrate how to configure logging to file in a docker environment.
Normaly, the Orthanc logs are going to stderr that is captured by the Docker engine.
However, when running Orthanc on a NAS with limited Docker tooling, it might be interesting to 
redirect logs to a folder that is mounted on the NAS.

# Description

This demo contains:

- an Orthanc container that is configured to store its logs in `/logs` folder thanks to the `LOGDIR` environment variable.
  We've also disabled logs deindentification thanks to the `DeidentifyLogs` option.  This is helpful, e.g in order to debug C-Find requests.

# Starting the setup

- To start the setup, type: `docker-compose up --build`

# demo

- Note: Since logging output is configured towards a folder, Orthanc will not output anything to stderr and therefore no output will be captured by Docker.
- logs are available on your host machine in `/tmp/orthanc-logs-docker/`
- if using `LOGDIR` you'll notice that a new log is created at each startup.
- Note: the `LOGDIR` and `LOGFILE` environment variables have been introduced in v 21.9.1 of the `orthancteam/orthanc` images.  Make sure to use a more recent version.
