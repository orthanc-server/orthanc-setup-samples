This repository contains sample Orthanc configurations to demonstrate how it can be configured in many use cases.  Right now, most of these samples use Docker to deploy Orthanc but some Windows setups are coming.
We also provide sample lua scripts.


# Docker setups

These sample setups require Docker to run.  They have been tested only on Linux systems.  To test one of these setups, clone this repository and check the readme file in each sample folder.


## Getting started
- [Basic Orthanc](docker/basic) to demonstrate a very basic Orthanc setup.
- [Various configuration](docker/all-usages) to demonstrate the different ways to configure the Docker images.
- [Stone Web Viewer](docker/stone-viewer) to demonstrate how to enable the [Stone Web Viewer plugin](https://book.orthanc-server.com/plugins/stone-webviewer.html).
- [Orthanc + PostgreSQL](docker/postgresql) to demonstrate how to use the Orthanc [PostgreSQL plugin](https://book.orthanc-server.com/plugins/postgresql.html)
- [Orthanc + MySQL](docker/mysql) to demonstrate how to use the Orthanc [MySQL plugin](https://book.orthanc-server.com/plugins/mysql.html)
- [Orthanc + MSSQL](docker/mssql) to demonstrate how to use the Orthanc [ODBC plugin](https://book.orthanc-server.com/plugins/odbc.html)
- [Orthanc basic DICOM association](docker/dicom-association) to demonstrate a simple DICOM association between Orthanc servers (and perform operations such as C-FIND, C-MOVE, C-STORE, C-ECHO).
- [Orthanc peering](docker/peering) to demonstrate Orthanc peering.
- [Orthanc dicom-web](docker/dicom-web) to demonstrate Orthanc dicom-web connectivity.
- [Orthanc + Transfers accelerator](docker/transfers-accelerator) to demonstrate Transfers accelerator plugin.
- [Orthanc basic HTTP authentication](docker/basic-authentication) to demonstrate static, basic HTTP authentication.
- [Orthanc Python plugin](docker/python) to demonstrate the use of the Python plugin.
- [Orthanc Indexer plugin](docker/indexer) to demonstrate the use of the Indexer plugin.
- [Sharing Orthanc configurations](docker/share-docker-compose-env-file) to demonstrate how to share configuration settings between multiple instance of Orthanc in the same Docker network.
- [Orthanc Tools JS](docker/orthanc-tools-js) to demonstrate the of [OrthancToolsJS](https://github.com/salimkanoun/Orthanc-Tools-JS/) tools developed by Salim Kanoun and his team.
- [Use Orthanc-Explorer-2](docker/oe2) to demonstrate how to use Orthanc-Explorer-2 with an `admin` and a standard `user` interface.
- [OHIF Viewer](docker/ohif) to demonstrate how to configure [OHIF Viewer](https://github.com/OHIF/Viewers) with Orthanc.
- [MedDream Viewer](docker/meddream) to demonstrate how to configure [MedDream Viewer](https://www.softneta.com/products/meddream-dicom-viewer/) with Orthanc.
- [Dcm4Chee](docker/dcm4chee5) to demonstrate how to interface Orthanc with Dcm4Chee 5, both using the DICOM protocol and the DICOMweb protocol.


## for advanced users
- [Dicom modification of received instances](docker/modify-instances) to demonstrate how to use Orthanc to modify incoming instances.
- [C-Find requests filtering](docker/dicom-cfind-filter-lua) to demonstrate how you can modify C-Find requests in a lua script.
- [Orthanc transcode middleman (lua)](docker/transcode-middleman) to demonstrate how to use Orthanc to change the TransferSyntax of instances inbetween a modality and a PACS.
- [Orthanc sanitizer middleman (python)](docker/sanitize-middleman-python) to demonstrate how to use Orthanc to sanitize instances between a modality and a PACS (modify tags + change the TransferSyntax).
- [Configure logging](docker/logs) to demonstrate how to configure logs into a folder that is mapped to the host.
- [Running Orthanc behind a nginx reverse proxy](docker/nginx) to demonstrate how to implement an Orthanc behind a reverse proxy.
- [Implementing HTTPS within orthanc](docker/https) to demonstrate how to implement HTTPS withing Orthanc.
- [Implementing HTTPS with nginx](docker/tls-with-nginx) to demonstrate how to implement an Orthanc behind nginx that is implementing TLS.
- [Use multiple Orthanc on the same DB](docker/multiple-orthancs-on-same-db) to demonstrate how to connect multiple Orthanc on the same PostgreSQL database and perform HTTP load balancing.
- [Use DICOM TLS](docker/dicom-tls) to demonstrate how to configure DICOM TLS between 2 Orthanc instances.
- [Download and update configuration dymically using Lua](docker/lua-download-config-and-restart) to demonstrate how to check and update configuration dymically using a lua script.
- [Health-check](docker/health-check) to monitor Orthanc and restart it if it becomes unresponsive.
- [Export studies to S3](docker/copy-to-S3) to export zipped studies into and S3 bucket.
- [Customize OE2 UI](docker/oe2-custom) to customize the logo and CSS of the Orthanc Explorer 2 User Interface.
- [Migrate from SQLite to PostgreSQL using the Advanced Storage plugin](docker/sqlite-to-postgresql) to demonstrate how to replace the SQLite DB by PostgreSQL without re-ingesting the whole DB.

## for software integrators
- [Orthanc + Serve-Folders Plugin](docker/serve-folders) to demonstrate how to use the Orthanc [Serve-Folders plugin](https://book.orthanc-server.com/plugins/serve-folders.html) to build custom web interface on top of Orthanc
- [Orthanc + Authorization Plugin + Osimis WebViewer](docker/authorization-plugin-viewer-query-args) to demonstrate how to use the Orthanc [authorization plugin](https://book.orthanc-server.com/plugins/authorization.html) with the [Osimis WebViewer plugin](https://bitbucket.org/osimis/osimis-webviewer-plugin/src/master/)
- [Authorization Plugin & access control](docker/access-control) to demonstrate how to use a python plugin and the authorization plugin to implement user access control at study level.
- [Orthanc mutual TLS authentication](docker/tls-mutual-auth) to demonstrate how to use client certificates to authentify Orthanc instances between them.
- [Orthanc mutual TLS authentication - 2](docker/full-tls) to demonstrate how to use client certificates to authentify Orthanc instances between them and to external web-services (note: very advanced users only !).  This sample uses nginx to implement
  server side TLS.
- [Orthanc on Azure](docker/azure) to demonstrate how to use the Orthanc in an Azure environment (using Azure SQL and Azure Blob Storage)
- [Orthanc on AWS](docker/aws) to demonstrate how to use the Orthanc in an AWS environment (using RDS and S3)
- [Orthanc on Minio](docker/minio) to demonstrate how to use the Orthanc with minio storage
- [Object-storage plugins performance tests](docker/performance-tests) to compare performance of VM SSDs vs object-storage plugins
- [Postgresql version upgrade](docker/postgresql-upgrade) to demontrate how to upgrade from one Postgresql version to another
- [Run orthanc as non-root user](docker/run-as-user) to demontrate how to run the orthancteam/orthanc image as a non root user
- [Job service](docker/job-service) to demonstrate how to run a side web-service to centralize the jobs of multiple Orthanc instances running behind a load balancer
- [Java plugin](docker/java) to demonstrate how to deploy a Java plugin

## for orthanc developers
- [Orthanc integration tests](docker/orthanc-integration-tests) to demonstrate how to run the [Orthanc integration tests](https://bitbucket.org/sjodogne/orthanc-tests)


# Windows

All these setups assume that Orthanc has been installed on your Windows OS at the default location.
Furthermore, the samples make use of the DCMTK toolkit that is assumed to be available in your path.
You might need to change a few path in the scripts in order to make them work on your system.

## for advanced users
- [Pre-fetching](windows/prefetching) to demonstrate how to trigger retrieval of prior studies


# Lua scripts

- [Dicom modification in OnStoredInstance](docker/modify-instances/modify.lua)
- [IncomingHttpRequestFilter](lua-samples/filter-http.lua)
- [Send to peer with retry](lua-samples/send-to-peer-with-retry.lua)
- [Pre-fetching](windows/prefetching/prefetching.lua)
- [Transcode and forward](docker/transcode-middleman/orthanc-middleman/transcodeAndForward.lua)
- [IncomingFindRequestFilter](docker/dicom-cfind-filter-lua/orthanc-b/cfind-filter.lua)
- [Notify external web service](docker/full-tls/orthanc-b/notify-external-web-service.lua)
- [Fix invalid UTF-8 tag values](lua-samples/sanitizeInvalidUtf8TagValues.lua)

# Python plugins

- [retry jobs](python-samples/job-retries.py)
- [pydicom integration](docker/python/orthanc/test.py)
- [show python functions/classes](python-samples/doc.py)
- [override /instances route](python-samples/override-instances-route.py)
- [Worklist server that implements MPPS](python-samples/worklist-with-mpps.py)
