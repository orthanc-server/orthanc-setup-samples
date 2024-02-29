# Purpose

This is a sample setup to demonstrate the usage of the DICOM TLS with Orthanc.

Note that this sample uses self-signed certificates.  In a real-life scenario,
the signing CA would probably be provided by your hospital IT or by an external certificate provider.

Certificates common names (orthanc-a-server and orthanc-b-server) are the names of the container services.

# Description

This demo contains:

- an Orthanc container simulating a PACS with TLS.
- 2 Orthanc containers connected to the same PostgreSQL DB.  One is implementing a DICOM endpoint with TLS
  and the other without TLS (a single Orthanc can not support both encrypted and non encrypted DICOM endpoint).
- an Orthanc container simulating a modality with TLS
- an Orthanc container simulating a modality without TLS


# Starting the setup

- First, you'll need to generate keys and certificates for all modules.  Go in the `tls` folder and type `./generate-tls.sh`
- To start the setup, type: `docker-compose up --force-recreate`

# demo

- The PACS with TLS is accessible at [http://localhost:8052/ui/app/](http://localhost:8052/ui/app/)
- The Orthanc with TLS UI is accessible at [http://localhost:8053/ui/app/](http://localhost:8053/ui/app/)
- The Orthanc without TLS UI is accessible at [http://localhost:8054/ui/app/](http://localhost:8054/ui/app/)
- The modality with TLS UI is accessible at [http://localhost:8055/ui/app/](http://localhost:8055/ui/app/)
- The modality without TLS UI is accessible at [http://localhost:8056/ui/app/](http://localhost:8056/ui/app/)
- upload a study to the modality with TLS ([http://localhost:8055/ui/app/](http://localhost:8055/ui/app/))
- once the study has been uploaded, send it to the `orthanc-with-tls` or to `orthanc-no-tls`.  This modality
  is able to communicate with both Orthanc (the modality is able to disable TLS when sending to the Orthanc without TLS).
- upload a study to the modality with TLS ([http://localhost:8056/ui/app/](http://localhost:8056/ui/app/))
- once the study has been uploaded, send it to the `orthanc-no-tls`.
- from this modality, you won't be able to send the study to the `orthanc-with-tls` since TLS is not configured on this modality.
- if you connect to any of the Orthanc UI, they will both show the 2 studies that have been received from both modalities.
- from the Orthanc with TLS UI, you may send a study to the PACS with TLS.
- from the modality with TLS UI, if you try to send a study directly to the `pacs-with-tls`, the transfer will fail
  because the certificate provided by the modality (acting as SCU) when connecting to the PACS is not trusted by the PACS (check the `./generate-tls.sh` script)
- from the PACS UI, if you try to send a study directly to the `modality-with-tls`, the transfer will fail
  because the certificate provided by the modality (acting as SCP) is not trusted by the PACS (acting as SCU).
  
