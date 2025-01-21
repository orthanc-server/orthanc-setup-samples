# Purpose

This is a sample setup to demonstrate how to configure DICOM assocations in Orthanc.

# Description

This demo contains:

- an `orthanc-a` container whose AET is ORTHANCA
- an `orthanc-b` container whose AET is ORTHANCB.  This container is configured to accept
  non-standard SOP Classes.

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

- first upload a file in Orthanc A through the UI [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/)
- browse to the study and, click "Send to remote modality", select "b"
- log in the Orthanc B user interface [http://localhost:8043/ui/app/](http://localhost:8043/ui/app/)
- check that the study has been received
- upload a new study in Orthanc B
- in the Orthanc A UI, you can then browse the remote orthanc B UI to find this study and retrieve it in orthanc A