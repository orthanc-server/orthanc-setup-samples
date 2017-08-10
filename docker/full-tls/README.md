# Purpose

This is a sample setup to demonstrate the usage of the Orthanc TLS (server side and usage of client certificates).

It also demonstrate how a Lua script executed in Orthanc can contact an external webservice using a client certificate.  Since
Orthanc does not currently allow Lua scripts to use client certificates, we have implemented a forward-proxy that is adding
the certificate to the requests between Orthanc and the external webservice.

# Description

This demo contains:

- an Orthanc-A container with the DicomWeb plugin enabled (as a client).
- an nginx-A container that will implement the TLS on the server side.  Orthanc-A is hidden behind a reverse-proxy.  This nginx server
accepts any connexion (no need for client certificate)
- an Orthanc-B container with the DicomWeb plugin enabled (as a server).  Each time this instance of Orthanc receives a DICOM instance,
it will send a message to the external-web-service from a Lua script.
- an nginx-B container that will implement the TLS on the server side.  Orthanc-B is hidden behind a reverse-proxy.  This nginx server only accepts connexions from clients with a client certificate that has been signed by a predefined root CA.
- a small external web service that Orthanc-B will contact from a lua script.  This web service is implemented in node.js.
- a small forward-proxy service that Orthanc-B will use when contacting the external-web-service.  This proxy is implemented in node.js.

# Starting the setup

- First, you'll need to generate keys and certificates for all modules.  Go in the `tls` folder and type `generate-tls.sh`
- Then, you'll have to copy all keys and certificates to docker volumes that will be used by containers.  In the `tls`folder, type `copy-tls-to-docker-volumes.sh`.
- To start the setup, type: `docker-compose up --build`

# demo


- Orthanc A is accessible at [https://localhost/orthanc/app/explorer.html](https://localhost/orthanc/app/explorer.html)
- Orthanc B is accessible at [https://localhost:843/orthanc/app/explorer.html](https://localhost:843/orthanc/app/explorer.html) although you won't have access to it since your browser HTTP client is not using a client certificate to connect to this site. 
- upload a study to Orthanc A
- once the study has been uploaded, send it to the `orthanc-b` remote modality.
- check the docker-compose logs.
