# Purpose

This is a sample setup to demonstrate how to configure the [OHIF viewer](https://github.com/OHIF/Viewers/) with Orthanc
and integrate it in the [Orthanc Explorer 2](https://book.orthanc-server.com/plugins/orthanc-explorer-2.html) user interface.

# Description

This demo contains:

- an Orthanc container.
- an nginx container that:
  - exposes the Orthanc UI on http://localhost/orthanc/ui/app/
  - serves the OHIF viewer on http://localhost/ohif
  - exposes the Orthanc API for the viewer on http://localhost/orthanc
  
# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Orthanc UI is accessible at [http://localhost/ui/app/](http://localhost/ui/app/) (no login/pwd)
- upload a study in Orthanc
- click on the `OHIF viewer` button to open the viewer



