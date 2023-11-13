# Purpose

This is a sample setup to demonstrate the usage of the Orthanc authorization plugin together with the DicomWeb plugin or the Rest API.
For a sample on how to integrate the Orthanc authorization plugin with Orthanc Explorer 2 and users, check [this sample](https://github.com/orthanc-team/orthanc-auth-service/tree/main/minimal-setup/keycloak).

An extra python plugin is added to filter QIDO-RS and tools/find results based on the users accessing the server
in order to list only the studies whom they have access to.

Note that all access control in the sample is performed based on the `InstitutionName` DICOM Tag.  Each user is supposed to belong
to one institution.  In order to have access to a study, its `InstitutionName` tag must exactly match the user institution.  Of course
you may implement other access control strategies.

In general, access control must be implemented in a custom web-service running next to Orthanc.  This web-service is used by the
[authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).

# Description

This demo contains:

- An `orthanc-for-admin` container connected to the same DB & storage with no access control configured.  This Orthanc instance is used
  by administrator with full access and by scripts with full access too.
- an `orthanc-for-clients` container with:
  - the [authorization plugin](https://book.orthanc-server.com/plugins/authorization.html) enabled.
  - a python plugin overwriting the `tools/find` route to return only the resources the user has access to
  - the OE2 user interface is not functional on this Orthanc since the auth-service is not implementing user profiles.
  Users are authenticated through an `api-key` header (not basic auth).  This Orthanc would typically be accessible from Dicom Web clients like Osirix.
- an `authorization-service` that Orthanc will request to grant access to its resources.  This autorization service would most likely be
  part of your web-app but should only be accessible to Orthanc (not from the external world).
- a PostgreSQL container to handle the Orthanc index DB.
- a Nginx container to act as a reverse proxy in-front of all Orthanc instances
- a third independant Orthanc instance acting as a populator to ingest test data into this setup

# Starting the setup

To start the setup, type: `docker-compose up --build`.  Note that the `orthanc-populator` should exit with code 0 after a few seconds; this is expected !  Once the populator has completed its task, you may use the system.

# demo

## Admin User: everything is allowed

- open the Admin interface at [http://localhost/orthanc-admin/ui/app/](http://localhost/orthanc-admin/ui/app/) (login/pwd: `admin`/`admin`)
- check the admin user has access to all studies (no authorization plugin or filter is configured on this Orthanc instance)
- this Orthanc instance is also used by the `authorization-service` to extract the `InstitutionName` tag from the study to perform
  access control cheks. (The auth-service has its own login/pwd too)
- you may also validate that standard users do not have access to this Orthanc instance (e.g login/pwd: `1`/`1`)

## User 1: access restricted to patients from his institution INST-1

User 1 has an `api-key` defined as `key-1`.

- User 1 can not list all studies:
  ```
  curl -v -H "api-key: key-1" http://localhost/orthanc-clients/studies
  ```
  This command shall return a 403 status code

- User 1 can access a study from INST-1:
  ```
  curl -H "api-key: key-1" http://localhost/orthanc-clients/studies/5206b0c2-42b14e52-eeb62c57-47ce6089-bf79000a
  ```

- User 1 can not access a study from INST-2:
  ```
  curl -v -H "api-key: key-1" http://localhost/orthanc-clients/studies/1fb6dd06-12004200-35b3c17f-4086c884-763e8f40
  ```
  This command shall return a 403 status code

- If User 1 wants to list all studies it has access to, it may issue a /tools/find:
  ```
  curl -H "api-key: key-1" http://localhost/orthanc-clients/tools/find -d '{"Level": "Study", "Query": {"PatientID": "*"}, "Expand": true }'
  ```
  This command shall return only the 3 studies from INST-1.


## API keys and dicom-web

- User 1 lists all studies it has access to through DicomWeb
  ```
  curl -v -H "api-key: key-1" http://localhost/orthanc-clients/dicom-web/studies?PatientID=*
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

