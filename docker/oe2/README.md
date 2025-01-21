# Purpose

This is a sample setup to demonstrate how to run Orthanc and configure the Orthanc-Explorer-2 User Interface.

The OE2 plugin is actually enabled by default in the `orthancteam/orthanc` Docker images.  Its configuration can be tuned
thanks to a number of [configuration options](https://github.com/orthanc-server/orthanc-explorer-2/blob/master/Plugin/DefaultConfiguration.json).

**Note**:  If you are looking for user management, have a look to this project: [orthanc-auth-service](https://github.com/orthanc-team/orthanc-auth-service).

# Description

This demo contains:

- 2 Orthanc containers connected to the same database.  One Orthanc has the default OE2 UI configured while the other
  has a custom configuration.
- 1 Orthanc container acting as a remote PACS remote accessible from DICOM or DICOMWeb.

- a nginx container that provides a web server on port 80.  It exposes the 3 Orthanc instances on theses subroutes
  -  [/orthanc-custom/](http://localhost/orthanc-custom/ui/app/).
  -  [/orthanc-default/](http://localhost/orthanc-default/ui/app/).
  -  [/pacs/](http://localhost/pacs/ui/app/).

- a Postgresql container to store the Orthanc database


# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- The customized Orthanc UI is accessible at [http://localhost/orthanc-custom/ui/app/](http://localhost/orthanc-custom/ui/app/).  Login/pwd = `demo/demo`
- The default Orthanc UI is accessible at [http://localhost/orthanc-default/ui/app/](http://localhost/orthanc-default/ui/app/).  No user/pwd.
- The PACS UI is accessible at [http://localhost/pacs/ui/app/](http://localhost/pacs/ui/app/).  No user/pwd.

You may upload multiple studies in the default Orthanc UI, transfer them to the remote Orthanc UI and then, play around with all the local and remote
browsing interfaces.
