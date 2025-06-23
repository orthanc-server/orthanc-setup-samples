# Purpose

This is a sample setup to demonstrate how to add a button into the GUI (at study level).
This button will create a worklist with the patient data of the selected study.


# Description

This demo contains:

- an Orthanc container which is built to add the orthanc-tools lib (https://pypi.org/project/orthanc-tools/)
- a Python plugin which is responsbiel for the worklist creation


# Starting the setup

- Create a `wl` folder aside compose file
- Start the setup thanks to this command: `docker compose up --build -d`

# demo

- Reach Orthanc UI at [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/)
- Upload a study
- Select the study and click on the calendar icon
- Browse to the `wl` folder, it should contain a `.wl` file
- if `DCMTK` is installed on your machine, try to query Orthanc for the worklists:
```
findscu -W -k "ScheduledProcedureStepSequence[0].Modality=" -k "PatientID=" 127.0.0.1 4242
```

