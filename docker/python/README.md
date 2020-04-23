# Purpose

This is a sample setup to demonstrate how to use the python plugin.

# Description

This demo contains:

- an Orthanc container with the Python plugin enabled
- a test.py script that extends the Orthanc Rest API with a 
  route calling pydicom and also adds 2 buttons in the
  Orthanc Explorer.

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- open your Orthanc Explorer on [http://localhost:8000](http://localhost:8000)
- upload a study
- browse the study, you'll now see a new button "show metadata"
- browse to an instance, you'll now see a button "show pydicom" that will call the new 
  API route you've defined.
