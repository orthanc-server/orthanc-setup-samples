# Purpose

This is a sample setup to demonstrate how to enable the Liveshare feature of the [Osimis WebViewer pro](http://www.osimis.io/en/blog/2016/10/14/plugin-osimis-pro-viewer.html).

# Description

This demo contains:

- a standard Orthanc container.
- a nginx container that serves as a reverse-proxy (this is mandatory in order to run the Liveshare)
- a liveshare container running the liveshare web-server that is required to exchange realtime info between all attendees.

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Connect to orthanc on [http://localhost/orthanc/](http://localhost/orthanc/).
- Upload an image to this instance of Orthanc.
- In the Orthanc explorer, open the study, and click on 'Osimis Web Viewer'
- In the Web Viewer, click on the 'liveshare' button to create a liveshare session.
- Follow the steps
- Once you have started a session, click the 'Invite' button.  Copy the provided url.
- Open a new browser window and paste the liveshare url in the address bar.
- Position both browser window on the same screen and see all actions performed by the 
  initiator are displayed on the attendee's browser