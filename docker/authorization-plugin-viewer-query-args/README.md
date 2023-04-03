# Purpose

This is a sample setup to demonstrate the usage of the Orthanc authorization plugin with the Osimis WebViewer plugin and the StoneViewer.

# Description

This demo contains:

- an Orthanc container with the [authorization plugin](https://book.orthanc-server.com/plugins/authorization.html) enabled.
- a small authorization micro service that Orthanc will request to authorize/forbids access to its resources.  This autorization service would most likely be part of your web-app but should only be accessible to Orthanc (not from the external world).

Note:  Since this sample was written, we have introduced a more advanced user management in the [orthanc-auth-service](https://github.com/orthanc-team/orthanc-auth-service).

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

## User 1: everything is allowed

- open a terminal and cd into the `dicomFiles` folder
- upload a sample file by adding a token in your request: `curl -v -X POST -H "token: good-token"  http://localhost:8042/instances --data-binary @anonymized1-MR-1-instance/MR000000.dcm`
- upload another sample file: `curl -v -X POST -H "token: good-token"  http://localhost:8042/instances --data-binary @anonymized2-MR-1-instance/MR000000.dcm`
- you can also check that you can request the Orthanc API: `curl -v -X GET -H "token: good-token"  http://localhost:8042/studies`
- Open this Osimis viewer url in your browser:[http://localhost:8042/osimis-viewer/app/index.html?study=ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2&token=good-token](http://localhost:8042/osimis-viewer/app/index.html?study=ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2&token=good-token)  
- Open this Stone viewer url in your browser:[http://localhost:8042/stone-webviewer/index.html?study=1.2.276.0.7230010.3.1.2.2831156000.1.1499097860.742568&token=good-token](http://localhost:8042/stone-webviewer/index.html?study=1.2.276.0.7230010.3.1.2.2831156000.1.1499097860.742568&token=good-token)  
- You are now 'logged in' as a user that has access to the whole app and data.  The `token=good-token` query argument is converted
  into an HTTP header when the viewer talks to the Orthanc API.

## User 2: access restricted to patient 1

- Open this url in your browser:[http://localhost:8042/osimis-viewer/app/index.html?study=ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2&token=restricted-token](http://localhost:8042/osimis-viewer/app/index.html?study=ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2&token=restricted-token)  
- You are now 'logged in' as a restricted user that can access only patient 1 data.
- Open this url in your browser:[http://localhost:8042/osimis-viewer/app/index.html?study=46d287d6-3f7f988f-18eca55f-7078bdf9-028e9a0b&token=restricted-token](http://localhost:8042/osimis-viewer/app/index.html?study=46d287d6-3f7f988f-18eca55f-7078bdf9-028e9a0b&token=restricted-token)  
- User 2 does not have access to patient 2 in the Osimis Viewer
- User 2 does not have a full access to the Orthanc API: `curl -v -X GET -H "token: restricted-token"  http://localhost:8042/studies`
- User 2 can however access to the API for everything that is related to Patient 1 `curl -v -X GET -H "token: restricted-token"  http://localhost:8042/studies/ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2` & `curl -v -X GET -H "token: restricted-token"  http://localhost:8042/patients/5c627243-c9c2acd8-6ad85563-2521e933-2394df24`

## User 3: no access at all

- Open this url in your browser:[http://localhost:8042/osimis-viewer/app/index.html?study=ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2&token=bad-token](http://localhost:8042/osimis-viewer/app/index.html?study=ad1d247b-6e0a0a02-98880beb-460a2261-d25594b2&token=bad-token)  
- You are now 'logged in' as a bad user that can not access anything.
- Open this url in your browser:[http://localhost:8042/osimis-viewer/app/index.html?study=46d287d6-3f7f988f-18eca55f-7078bdf9-028e9a0b&token=bad-token](http://localhost:8042/osimis-viewer/app/index.html?study=46d287d6-3f7f988f-18eca55f-7078bdf9-028e9a0b&token=bad-token)  
- User 3 does not have access to patient 1 & 2
- You can also check that User 3 does not have access at all to the Orthanc API: `curl -v -X GET -H "token: bad-token"  http://localhost:8042/studies`




