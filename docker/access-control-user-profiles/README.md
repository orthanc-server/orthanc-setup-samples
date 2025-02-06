This is a work in progress  !!!


# Purpose

This is a sample setup based on discussions in https://discourse.orthanc-server.org/t/user-based-access-control-with-label-based-resource-access/5454.

The auth-plugin is used with Basic HTTP authentication enabled.
When a user uploads a DICOM file, it is directly labeled with its username.  However, the integration with OE2 is not
perfect so you need to reload the OE2 interface after the upload to have access to the newly updated study.
The auth-service only implements the user-profile route which is actually sufficient since, e.g., when opening a viewer in a new tab,
the browser keeps the basic auth headers (which is not happening when using other headers for authentication).

# Description

# Starting the setup

To start the setup, type: `docker-compose up --build`.  

# demo

## Admin User: everything is allowed

- open the Admin interface at [http://localhost/orthanc-admin/ui/app/](http://localhost/orthanc-admin/ui/app/) (login/pwd: `admin`/`admin`)
- check the admin user has access to all studies (no authorization plugin or filter is configured on this Orthanc instance)

## Standard User:

- open the User interface at [http://localhost/orthanc-users/ui/app/](http://localhost/orthanc-users/ui/app/) (login/pwd: `user1`/`user1`)
- upload a study
- reload the UI
- check the study has been labeled with the user name
- download the study -> it should be allowed
- unfortunately, opening a viewer currently does not work
