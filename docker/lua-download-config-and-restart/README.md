# Purpose

This is a sample setup to demonstrate how to download and apply a new Orthanc configuration dynamically
thanks to a lua script.

# Description

This demo contains:

- an Orthanc container with a lua script.
- a sample webservice providing a new configuration to Orthanc every minute.

The Lua scripts checks for a new configuration at startup and, then, on the Lua Heart Beat callback.
If the webservice provides a new configuration, the lua scripts saves it to disk and tells Orthanc
to restart using the new configuration.

Note that we've split the Orthanc configuration between a `fixed` configuration that is not updated
and a `dynamic` configuration that is provided by the webservice.


# Starting the setup

To start the setup, type: `docker-compose up --build`.

# demo

- check in the logs that the config is checked every 30 seconds and updated every 60 seconds
- Open the Orthanc UI and check that the Orthanc Name changes every minute
- stop the webservice container and check that Orthanc continues to run even when the webservice is down: `docker-compose stop config-webservice`
