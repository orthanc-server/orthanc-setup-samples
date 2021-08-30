# Purpose

This is a sample setup to demonstrate the usage of the DICOM TLS with Orthanc.

Note that this sample uses self-signed certificates.  In a real-life scenario,
the signing CA would probably be provided by your hospital IT or by an external certificate provider.

Certificates common names (orthanc-a-server and orthanc-b-server) are the names of the container services.

# Description

This demo contains:

- an Orthanc-A container.
- an Orthanc-B container.

# Starting the setup

- First, you'll need to generate keys and certificates for all modules.  Go in the `tls` folder and type `generate-tls.sh`
- To start the setup, type: `docker-compose up --build`

# demo

- Orthanc A is accessible at [http://localhost:8042/orthanc/app/explorer.html](http://localhost:8042/orthanc/app/explorer.html)
- Orthanc B is accessible at [http://localhost:8043/orthanc/app/explorer.html](http://localhost:8043/orthanc/app/explorer.html)
- upload a study to Orthanc B
- once the study has been uploaded, send it to the `orthanc-a` remote modality.
- check the docker-compose logs.
