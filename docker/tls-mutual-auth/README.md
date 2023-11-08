# Purpose

This is a sample setup to demonstrate the usage of the Orthanc TLS (server side and usage of client certificates).

# Description

This demo contains:

- an Orthanc-A container with the DicomWeb plugin enabled.
- an Orthanc-B container with the DicomWeb plugin enabled.  Orthanc B will implement an HTTPS server with client authentication enabled.

# Starting the setup

- First, you'll need to generate keys and certificates for all modules.  Go in the `tls` folder and type `generate-tls.sh`
- To start the setup, type: `docker-compose up --build`

# demo

- Orthanc A is accessible at [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/)
- Orthanc B is accessible at [https://localhost:8043/ui/app/](https://localhost:8043/ui/app/) although you won't have access to it since your browser HTTP client is not using a client certificate to connect to this site. 
- you may check the connectivity at [http://localhost:8042/connectivity-checks/app/index.html](http://localhost:8042/connectivity-checks/app/index.html)
- upload a study to Orthanc A
- once the study has been uploaded, send it to the `orthanc-b` remote modality to use Orthanc peering.
- once the study has been uploaded, send it to the `orthanc-b` remote dicom-web server to use Dicom-web.
- check the docker-compose logs.
- note that you can access the orthanc-b API with curl `curl --insecure --cert ./tls/client-crt.pem --key ./tls/client-key.pem -v https://localhost:8043/system`