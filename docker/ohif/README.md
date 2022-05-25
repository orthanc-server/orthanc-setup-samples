# Purpose

This is a sample setup to demonstrate how to configure the [OHIF viewer](https://github.com/OHIF/Viewers/) with Orthanc
and integrate it in the [Orthanc Explorer 2](https://book.orthanc-server.com/plugins/orthanc-explorer-2.html) user interface.

# Description

It seems it's not straightforward to have OHIF running at a subroute without recompiling it when setting the PUBLIC_URL env var.
Therefore, this setup exposes the OHIF viewer on a different server than Orthanc.  In a production environment, you can 
certainly run Orthanc UI on https://orthanc.my.site/ and the viewer on https://viewer.my.site/ such that it is served at `/` (and the viewer at `/Viewer`).

However, to avoid CORS issues, orthanc API is exposed to OHIF as an `/orthanc` subroute on the `viewer` server.

This demo contains:

- an Orthanc container.
- an nginx container that:
  - exposes the Orthanc UI on http://localhost:80
  - serves the OHIF viewer on http://localhost:81
  - exposes the Orthanc API for the viewer on http://localhost:81/orthanc
  
# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Orthanc UI is accessible at [http://localhost/ui/app/](http://localhost/ui/app/) (`demo:demo`)
- upload a study in Orthanc
- click on the `OHIF viewer` button to open the viewer


# Notes

- OHIF code contains a `.mjs` file that is not recognized by nginx -> we need to provie a custom `mime.types` file.

