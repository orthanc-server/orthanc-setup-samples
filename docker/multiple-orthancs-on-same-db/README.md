# Purpose

This is a sample setup to demonstrate how to configure multiple Orthancs with a
single PostgreSQL database.

This sample also demonstrates how to configure an HTTP load balancer in front of
multiple Orthanc instances.

Check [this page](https://book.orthanc-server.com/faq/scalability.htm#concurrent-accesses-to-the-db-in-orthanc-1-9-2) on the Orthanc book for more information about this.

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
  files are stored in a shared Docker volume)


All 3 orthanc instances are sharing the same data since they are using the same DB and storage.
# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- login/pwd = demo/demo
- Orthanc HTTP A is accessible at [http://localhost/orthanc-a/app/explorer.html](http://localhost/orthanc-a/app/explorer.html)
- Orthanc HTTP B is accessible at [http://localhost/orthanc-b/app/explorer.html](http://localhost/orthanc-b/app/explorer.html)
- Load balanced Orthancs are accessible at [http://localhost/orthanc-lb/app/explorer.html](http://localhost/orthanc-lb/app/explorer.html)
- if you open the Load balanced Orthancs and refresh the page, you should see that it alternatively reach Orthanc A & B.
- upload a study to the load balanced Orthanc [http://localhost/orthanc-lb/app/explorer.html#upload](http://localhost/orthanc-lb/app/explorer.html#upload).
- check the study appears both on Orthanc A, Orthanc B and the load balanced Orthancs
