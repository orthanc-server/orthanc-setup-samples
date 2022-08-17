# Purpose

This is a sample setup to demonstrate the usage of the Orthanc authorization plugin together with the DicomWeb plugin.
Furthermore, an extra python plugin is added to filter QIDO-RS and tools/find results based on the users accessing the server
in order to list only the studies whom they have access to.

Note that all access control in the sample is performed based on the `InstitutionName` DICOM Tag.  Each user is supposed to belong
to one institution.  In order to have access to a study, its `InstitutionName` tag must exactly match the user institution.  Of course
you may implement other access control strategies.

In general, access control must be implemented in a custom web-service running next to Orthanc.  This web-service is used by the
[authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).

# Description

This demo contains:

- an `orthanc-for-users` container with:
  - the [authorization plugin](https://book.orthanc-server.com/plugins/authorization.html) enabled.
  - a python plugin overwriting the `tools/find` route to return only the resources the user has access to
- an `authorization-service` that Orthanc will request to grant access to its resources.  This autorization service would most likely be
  part of your web-app but should only be accessible to Orthanc (not from the external world).
- another `orthanc-for-admin` container connected to the same DB & storage with no object access control.  This Orthanc instance is used
  by administrator with full access and by scripts with full access too.
- another `orthanc-for-clients` container which is almost identical to `orthanc-for-users` although it does not provide any user interface
  and authenticate users through an `api-key` header (not basic auth)
- a PostgreSQL container to handle the Orthanc index DB.
- a Nginx container to act as a reverse proxy in-front of all Orthanc instances
- a third independant Orthanc instance acting as a populator to ingest test data into this setup

# Starting the setup

To start the setup, type: `docker-compose up --build`.  Note that the `orthanc-populator` should exit with code 0 after a few seconds; this is expected !  Once the populator has completed its task, you may use the system.

# demo

## Admin User: everything is allowed

- open the Admin interface at [http://localhost/orthanc-admin/ui/app/](http://localhost/orthanc-admin/ui/app/) (login/pwd: `admin`/`admin`)
- check the admin user has access to all studies (no authorization plugin or filter is configured on this Orthanc instance)
- this Orthanc instance is also used by the `authorization-service` (it has its own login/pwd too)
- you may also validate that standard users do not have access to this Orthanc instance (e.g login/pwd: `1`/`1`)

## User 1: access restricted to patients from his institution INST-1

- In an incognito browser, open the User interface at [http://localhost/orthanc-users/ui/app/](http://localhost/orthanc-users/ui/app/) (login/pwd: `1`/`1`)
- You should only see the patients from INST-1: `1-A` and `1-B`

## User 2: access restricted to patients from his institution INST-2

- In an incognito browser, open the User interface at [http://localhost/orthanc-users/ui/app/](http://localhost/orthanc-users/ui/app/) (login/pwd: `2`/`2`)
- You should only see the patients from INST-1: `2-C` and `2-D`

## API keys

- User 1 has an `api-key` defined as `key-1`.  You may also issue some HTTP requests for this user to validate authorizations:
  ```
  curl -H "api-key: key-1" http://localhost/orthanc-clients/tools/find -d '{"Level": "Study", "Query": {"PatientID": "*"}, "Expand": true }'
  ```
  This command shall return 3 studies.

- User 2 has an `api-key` defined as `key-2`:
  ```
  curl -H "api-key: key-2" http://localhost/orthanc-clients/tools/find -d '{"Level": "Study", "Query": {"PatientID": "*"}, "Expand": true }'
  ```
  This command shall return 2 studies.


## API keys and dicom-web

- User 1 lists all studies it has access to through DicomWeb
  ```
  curl -H "api-key: key-1" http://localhost/orthanc-clients/dicom-web/studies?PatientID=*
  ```
  This command shall return 3 studies

- User 1 accesses a specific study it has access to.
  ```
  curl -H "api-key: key-1" http://localhost/orthanc-clients/dicom-web/studies/1.1 --output /tmp/study1.1.zip
  ```

- User 2 tries to access the same study (which is not accessible to him).
  ```
  curl  -v -H "api-key: key-2" http://localhost/orthanc-clients/dicom-web/studies/1.1
  ```
  This command shall return a 403 status code.

## Code explained

### plugin.py

This code runs as a plugin inside Orthanc (`orthanc-for-users` and `orthanc-for-clients`).
Its main task is to override the `tools/find` route that is used by the Orthanc Explorer 2 interface and by the DicomWeb plugin.

Note that this sample code only handles `tools/find` at `Study` level (not `Series`, `Patient` or `Instance`).  This could be implemented though.

It can work in 3 modes (2 of them being implemented in the sample setup).  Some of these modes can be combined e.g `modify-query` & `filter-results`.  These modes can be adapted by changing the `FILTER_MODE` environment variable in the `docker-compose.yml` file

#### FILTER_MODE = modify-query

Since, in this sample, access control is performed based on the `InstitutionName` tag, the plugin actually adds a filter
on this `InstitutionName` tag before calling the `tools/find` route from the core Orthanc.  For this, the plugin must call
the external webservice to retrieve the institution the user belongs to.

#### FILTER_MODE = external

In this mode (not implemented in this demo), the whole `tools/find` behaviour is implemented in an external webservice.  This 
web-service will likely have its own DB with the studies DICOM tags.  This is the most generic mode but requires a lot of work
in the external web-service.

#### FILTER_MODE = filter-results

This mode is more generic (it could implement an access control philosophy that is not based on the `InstitutionName`).
The plugin first call the core `tools/find` route and then, for each study returned, it checks, via the external authorization web-service,
if the user can access this study.  If not, the study is removed from the answers.
This is not efficient in terms of performance and won't scale if there are numerous users and studies.

