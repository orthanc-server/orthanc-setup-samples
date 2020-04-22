# Purpose

This is a sample setup to demonstrate how an Orthanc instance can be used to modify instances received from a modality.
In this very simple example, we consider that the InstitutionName Dicom TAG is wrong in the images coming from the modality
and we want to standardize it in the Orthanc storage.  We also want to remove the OperatorsName from the images.

# Description

This demo contains:

- an Orthanc-modality container that simulates a modality. 
- an Orthanc that is acting as a PACS.

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- login/pwd = demo/demo
- Connect to the orthanc simulating the modality on [http://locdemoalhost:8044](http://localhost:8044 login/pwd: demo/demo).
- Upload an image to this instance of Orthanc.
- In the Orthanc explorer, open the study, select 'send to pacs' and send
- the instance is forwarded to the pacs that will modify the InstitutionName on reception
- Open the orthanc acting as a PACS on [http://localhost:8042](http://localhost:8042 login/pwd: demo/demo) and check that the InstitutionName has changed.

