# Purpose

This is a sample setup to demonstrate how to configure multiple Orthancs with a
single PostgreSQL database. This should allow to improve performances.

This sample also demonstrates how to configure an HTTP load balancer in front of
multiple Orthanc instances.  Note that this load balancing is applied to
to GET requests only right now (until [issue 83](https://bitbucket.org/sjodogne/orthanc/issues/83/serverindex-shall-implement-retries-for-db) is fixed).

# Description

This demo contains:

- an Orthanc DICOM container (orthanc-dicom) that is exposing only its
  DICOM port (and not the HTTP port).
- two Orthanc HTTP containers (orthanc-http-a&b) that are actually not 
  exposing any port to the public since they are positioned behind a
  nginx reverse proxy (and load balancer)
- a nginx container that performs load balancing and exposes all orthanc
  on the same domain.
- a PostgreSQL container that will store the Orthanc Index DB (the dicom
  files are stored in a Docker volume)

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Orthanc HTTP A is accessible at [http://localhost/orthanc-a/app/explorer.html](http://localhost/orthanc-a/app/explorer.html)
- Orthanc HTTP B is accessible at [http://localhost/orthanc-b/app/explorer.html](http://localhost/orthanc-b/app/explorer.html)
- Load balanced Orthancs are accessible at [http://localhost/orthanc-lb/app/explorer.html](http://localhost/orthanc-lb/app/explorer.html)
- if you open the Load balanced Orthancs and refresh the page, you should see that it alternatively reach Orthanc A & B.
- upload a study to the load balanced Orthanc [http://localhost/orthanc-lb/app/explorer.html#upload](http://localhost/orthanc-lb/app/explorer.html#upload).  The HTTP requests will be forwarded to orthanc HTTP A but will be stored in the shared DB.
- check the study appears both on Orthanc A, Orthanc B and the load balanced Orthancs
