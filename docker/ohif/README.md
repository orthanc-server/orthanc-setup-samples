# Purpose

This is a sample setup to demonstrate how to configure the [OHIF viewer](https://github.com/OHIF/Viewers/) with Orthanc
and integrate it in the [Orthanc Explorer 2](https://book.orthanc-server.com/plugins/orthanc-explorer-2.html) user interface.

Note that there are 2 ways to integrate with OHIF.  If you want to use your custom version of OHIF, we recommend to build
a container and run it outside Orthanc.  If you want to use the default OHIF viewer, simply use the [OHIF plugin](https://book.orthanc-server.com/plugins/ohif.html) that is
running insdie Orthanc.
# Description

This demo contains:

- 2 Orthanc containers, one running the OHIF plugin and one integrating with the OHIF viewer hosted by the nginx container..
- an nginx container that:
  - exposes the Orthanc UI on http://localhost/orthanc-container/ui/app/ and http://localhost/orthanc-plugin/ui/app/
  - serves the OHIF viewer (e.g, a more recent version than the one packaged in the plugin)
  - exposes the Orthanc API for the viewer on http://localhost/orthanc
  
# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Orthanc UI is accessible at [http://localhost/orthanc-container/ui/app/](http://localhost/orthanc-container/ui/app/) and [http://localhost/orthanc-plugin/ui/app/](http://localhost/orthanc-plugin/ui/app/) (no login/pwd)
- upload a study in Orthanc
- click on the `OHIF viewer` button to open the viewer



