# Purpose

This is a sample setup to demonstrate the usage of the Orthanc authorization plugin.

# Description

This demo contains:
- an Orthanc container with the [authorization plugin](http://book.orthanc-server.com/plugins/authorization.html) enabled.
- an nginx container that simulates a web app that is using Orthanc as one of its backend component.  This web app implements some kind of authentication.  Once a user is logged in the web app, the app sets `my-auth-header` HTTP headers.
Orthanc is hidden behind a reverse-proxy.  This reverse-proxy adds the authorization headers to every request that is sent to Orthanc.
- a small authorization micro service that will Orthanc will contact to authorize/forbids access to its resources.  This autorization service would most likely be part of your web-app but should only be accessible to Orthanc (not from the external world).

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

## User 1: everything is allowed

Open this url in your browser:[http://localhost/orthanc-allowed/app/explorer.html](http://localhost/orthanc-allowed/app/explorer.html).  Now you are 'logged in' as a full power user that has access to the whole app.
Go to the upload page and upload the 2 MR files available in `dicomFiles/anonymized1-MR-1-instance` and `dicomFiles/anonymized2-MR-1-instance`.

Once the files have been uploaded, you may access the orthanc explorer and visualize all studies.

## User 2: access restricted to patient 1

Open this url in your browser:[http://localhost/orthanc-restricted/app/explorer.html](http://localhost/orthanc-restricted/app/explorer.html).  Now you are 'logged in' as a restricted user that has access only to patient 1.
This user won't be able to list all users from the Orthanc explorer interface but has access to the patient 1 page when referred directly to the right page [http://localhost/orthanc-restricted/app/explorer.html#patient?uuid=5c627243-c9c2acd8-6ad85563-2521e933-2394df24](http://localhost/orthanc-restricted/app/explorer.html#patient?uuid=5c627243-c9c2acd8-6ad85563-2521e933-2394df24)

## User 3: no access at all

Open this url in your browser:[http://localhost/orthanc-forbidden/app/explorer.html](http://localhost/orthanc-forbidden/app/explorer.html).  Now you are 'logged in' as a user that can not access any resources.
This user won't be able to list all users from the Orthanc explorer interface so, Orthanc basically seems empty to him.




