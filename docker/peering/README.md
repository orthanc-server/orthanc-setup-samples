
# Purpose

This is a sample setup to demonstrate how to transfer data between 2 Orthancs over HTTP 
using the peering mechanism.  

# Description

This demo contains:

- two Orthanc containers

# Starting the setup

- To start the setup, type: `docker-compose up --build`

# demo

- login/pwd for web interfaces: demo/demo
- Orthanc A is accessible at [http://localhost:8042](http://localhost:8042)
- Orthanc B is accessible at [http://localhost:8043](https://localhost:8043)
- upload a study to Orthanc A
- once the study has been uploaded, in the UI, send it to the `orthanc-b` remote modality.  This transfer is performed over HTTP.
- connect to Orthanc B to verify it has been transmitted.
