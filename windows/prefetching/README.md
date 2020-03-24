# Purpose

This is a sample setup to demonstrate how to trigger pre-fetching of prior studies when an Orthanc receives a study.

# Description

This demo contains:

- an Orthanc "PACS" that simulates a PACS
- an Orthanc "WORKSTATION that simulates a radiology Workstation that is receiving examsn from the PACS
- an Orthanc "Middleman" that lies between the PACS and the Workstation

# Starting the setup

To start the setup, type: `./start.ps1`.  This will start 3 orthanc and push two studies in the PACS (a "current" one and a "previous" one)

# demo

Connect to the PACS web interface on [http://localhost:8245](http://localhost:8245)

- open the latest study and click "Send to modality", send it to the middleman

After a few seconds, connect to the Workstation web interface on [http://localhost:8247](http://localhost:8247)

- you should now see 2 studies there (the one you've sent to the middleman and the oldest one)

At the end of the demo:

- the PACS should still contain the 2 studies
- the middleman shall be empty
- the workstation shall contain the 2 studies too