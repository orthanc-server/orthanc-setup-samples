# Purpose

This is a sample setup to demonstrate how to reconfigure the storage
directory inside the container. You would normally never need to do it;
the recommended method is to simply map the default storage directory to
a Docker volume.

# Starting the setup

To start the setup, type: `docker-compose up --build`

# Demo

Observe the selected Orthanc Storage and Index directory in the log:

orthanc_1  | W0828 08:29:25.366004 OrthancInitialization.cpp:1018] SQLite index directory: "/mnt"
orthanc_1  | W0828 08:29:25.366871 OrthancInitialization.cpp:1088] Storage directory: "/mnt"
