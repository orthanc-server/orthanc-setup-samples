# Purpose

This is a sample setup to demonstrate how to configure Orthanc behind an Nginx server.

Nginx will implement the TLS (HTTPS to HTTP conversion) and will expose multiple Orthanc 
on the same hostname and port (in this case, port 443).

This demo will also show you how to configure an Orthanc peer to accept the self-signed 
certificate of the Orthanc peer to which it connects via HTTPS.

Furthermore, it will also show you how you can make your Orthanc Rest API `readonly` by 
allowing only the GET requests to orthanc-C.

# Description

This demo contains:

- an Nginx container that implements TLS and a reverse proxy to 3 Orthanc instances
- an Orthanc-A container.
- an Orthanc-B container.
- an Orthanc-C container that is made readonly by the reverse proxy

# Starting the setup

- First, you'll need to generate keys and certificates for all modules.  Go in the `tls` folder and type `generate-tls.sh`
- Then, you'll have to copy all keys and certificates to docker volumes that will be used by the nginx container.  In the `tls`folder, type `copy-tls-to-docker-volumes.sh`.
- To start the setup, type: `docker-compose up --build`

# demo

- Orthanc A is accessible at [https://localhost/orthanc-a/app/explorer.html](https://localhost/orthanc-a/app/explorer.html)
- Orthanc B is accessible at [https://localhost/orthanc-b/app/explorer.html](https://localhost/orthanc-b/app/explorer.html)
- Orthanc C is accessible at [https://localhost/orthanc-c/app/explorer.html](https://localhost/orthanc-c/app/explorer.html)
- Orthanc A is not accessible at [http://localhost:8042](http://localhost:8042) because it does not expose its HTTP port to the exterior of the Docker network
- upload a study to Orthanc A
- once the study has been uploaded, send it to the `orthanc-b-https` remote modality.  This transfer is performed over HTTPS.  We have configured Orthanc A to recognize the certificates of Orthanc B.
- connect to Orthanc B to verify it has been transmitted.
- from Orthanc A, send the study to the `orthanc-c-dicom` remote modality.  This transfer is performed over DICOM protocol.
- connect to the Orthanc C interface and try to delete the patient. It shall be forbidden by nginx since it allows only the GET requests.
