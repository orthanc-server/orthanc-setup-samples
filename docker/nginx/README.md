# Purpose

This is a sample setup to demonstrate how to run orthanc behind a nginx reverse proxy.

# Description

This demo contains:

- a nginx container that provides a web server on port 80.  It exposes Orthanc on the subroute [/orthanc/](http://localhost:/orthanc/).
- an orthanc container

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- login/pwd = demo/demo
- Orthanc is accessible at [http://localhost/orthanc/app/explorer.html](http://localhost/orthanc/app/explorer.html)
