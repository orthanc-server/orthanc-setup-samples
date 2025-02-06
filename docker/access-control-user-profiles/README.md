# Purpose

This is a sample setup based on discussions in https://discourse.orthanc-server.org/t/user-based-access-control-with-label-based-resource-access/5454.

The auth-plugin is used with Basic HTTP authentication enabled.

When a user uploads a DICOM file, it is directly labeled with its username.  However, the integration with OE2 is not
perfect so you need to reload the OE2 interface after the upload to have access to the newly updated study.

The auth-service only implements the user-profile route which is actually sufficient since, e.g., when opening a viewer in a new tab,
the browser keeps the basic auth headers (which is not happening when using other headers for authentication).

Unfortunately, it is not easy to logout because the browser remembers the last user+pwd -> try it in incognito mode.


# Description

# Starting the setup

To start the setup, type: `docker-compose up --build`.  

# demo

## Admin User: everything is allowed

- In an incognito tab, open User interface interface at [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/) (login/pwd: `admin`/`admin`)
- check the admin user has access to all studies

## Standard User:

- In another browser incognito tab, open the User interface at [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/) (login/pwd: `user1`/`user1`)
- upload a study
- reload the UI
- check the study has been labeled with the user name
- download the study -> it should be allowed
- open the study in StoneViewer -> it should be allowed
- from the admin UI, copy a url to a viewer to a study `user1` should not have access to and copy it in this browser address bar -> the `user1` should not have access to that study
