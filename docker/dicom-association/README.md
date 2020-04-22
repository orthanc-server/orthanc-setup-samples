To start, use `docker-compose up --build -d`.
To stop, use `docker-compose down`.

As described in the `docker-compose.yml` file, Orthanc's HTTP server is
reachable via port 80 on the Docker host, and Orthanc's DICOM server is
reachable via port 104 on the Docker host.





# Purpose

This is a sample setup to demonstrate how to configure DICOM assocations in Orthanc.

# Description

This demo contains:

- an Orthanc container whose AET is ORTHANCA
- an Orthanc container whose AET is ORTHANCB

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

- first upload a file in Orthanc A through the Rest API using this curl command or via the interface:
  `curl -v -X POST http://demo:demo@localhost:80/instances --data-binary @anonymized1-MR-1-instance/MR000000.dcm`  
- log in the Orthanc A user interface [http://localhost/](http://localhost/); login/pwd = demo/demo.
- browse to the study and, click "Send to remote modality", select "b"
- log in the Orthanc B user interface [http://localhost:81/](http://localhost:81/); login/pwd = demo/demo.
- check that the study has been received