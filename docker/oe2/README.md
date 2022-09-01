# Purpose

This is a sample setup to demonstrate how to run Orthanc-Explorer-2 behind a reverse proxy.

As of version 0.4.0, there's no real user management in Orthanc-Explorer-2 but you can
simulate this by having 2 orthanc running on the same DB.  One Orthanc is accessible to admin
users with full access to the UI and API while another Orthanc is accessible to users with reduced
functionality and UI.

**Disclaimer**: this sample is provided 'as is' without any guarantee.  Don't use it in production unless you perfectly understand every part of it.

# Description

This demo contains:

- a nginx container that provides a web server on port 80.  It exposes the 3 Orthanc instances on theses subroutes
  -  [/orthanc-admin/](http://localhost/orthanc-admin/ui/app/).
  -  [/orthanc-users/](http://localhost/orthanc-users/ui/app/).
  -  [/pacs/](http://localhost/pacs/ui/app/).

- 3 Orthanc containers, one configured for `admin` and one configured for `users` and one configured as an external pacs
- a Postgresql container to store the Orthanc database

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Orthanc UI with full admin access is accessible at [http://localhost/orthanc-admin/ui/app/](http://localhost/orthanc-admin/ui/app/).  Login/pwd = `admin/admin`
- Orthanc UI with reduced user access is accessible at [http://localhost/orthanc-users/ui/app/](http://localhost/orthanc-users/ui/app/).  Login/pwd = `user/user`
- Orthanc UI for the PACS is accessible at [http://localhost/pacs/ui/app/](http://localhost/pacs/ui/app/).  No login required.
