This repository contains sample Orthanc configurations to demonstrate how it can be configured in many use cases.  Right now, most of these samples use Docker to deploy Orthanc but some Windows setups are coming.
We also provide sample lua scripts.

Content:

[TOC]


# Docker setups

These sample setups require Docker to run.  They have been tested only on Linux systems.  To test one of these setups, clone this repository and check the readme file in each sample folder.

Note that, from tag 20.4.2, the osimis/orthanc images that are used here have changed a lot.  All these demo setups have been updated to work with these images.  They
won't work with previous images.  Go back in the git history of this repo to get setups for older images.

## Getting started
- [Basic Orthanc](docker/basic) to demonstrate a very basic Orthanc setup.
- [Orthanc + PostgreSQL](docker/postgresql) to demonstrate how to use the Orthanc [PostgreSQL plugin](http://book.orthanc-server.com/plugins/postgresql.html)
- [Various configuration](docker/all-usages) to demonstrate the different ways to configure the Docker images.
- [Orthanc + MySQL](docker/mysql) to demonstrate how to use the Orthanc [MySQL plugin](http://book.orthanc-server.com/plugins/mysql.html)
- [Orthanc basic DICOM association](docker/dicom-association) to demonstrate a simple DICOM association between Orthanc servers (and perform operations such as C-FIND, C-MOVE, C-STORE, C-ECHO).
- [Orthanc peering](docker/peering) to demonstrate Orthanc peering.
- [Orthanc dicom-web](docker/dicom-web) to demonstrate Orthanc dicom-web connectivity.
- [Orthanc + Transfers accelerator](docker/transfers-accelerator) to demonstrate Transfers accelerator plugin.
- [Orthanc basic HTTP authentication](docker/basic-authentication) to demonstrate static, basic HTTP authentication.
- [Orthanc Python plugin](docker/python) to demonstrate the use of the Python plugin.
- [Sharing Orthanc configurations](docker/share-docker-compose-env-file) to demonstrate how to share configuration settings between multiple instance of Orthanc in the same Docker network.

## for advanced users
- [Dicom modification of received instances](docker/modify-instances) to demonstrate how to use Orthanc to modify incoming instances.
- [C-Find requests filtering](docker/dicom-cfind-filter-lua) to demonstrate how you can modify C-Find requests in a lua script.
- [Orthanc transcode middleman (lua)](docker/transcode-middleman) to demonstrate how to use Orthanc to change the TransferSyntax of instances inbetween a modality and a PACS.
- [Orthanc sanitizer middleman (python)](docker/sanitize-middleman-python) to demonstrate how to use Orthanc to sanitize instances between a modality and a PACS (modify tags + change the TransferSyntax).
- [Implementing HTTPS with nginx](docker/tls-with-nginx) to demonstrate how to implement an Orthanc behind a reverse proxy.
- [Use multiple Orthanc on the same DB](docker/multiple-orthancs-on-same-db) to demonstrate how to connect multiple Orthanc on the same PostgreSQL database and perform HTTP load balancing.

## for software integrators
- [Orthanc + Serve-Folders Plugin](docker/serve-folders) to demonstrate how to use the Orthanc [Serve-Folders plugin](http://book.orthanc-server.com/plugins/serve-folders.html) to build custom web interface on top of Orthanc
- [Orthanc + Authorization Plugin + Osimis WebViewer](docker/authorization-plugin-viewer-query-args) to demonstrate how to use the Orthanc [authorization plugin](http://book.orthanc-server.com/plugins/authorization.html) with the [Osimis WebViewer plugin](https://bitbucket.org/osimis/osimis-webviewer-plugin/src/master/)
- [Orthanc mutual TLS authentication](docker/tls-mutual-auth) to demonstrate how to use client certificates to authentify Orthanc instances between them.
- [Orthanc mutual TLS authentication - 2](docker/full-tls) to demonstrate how to use client certificates to authentify Orthanc instances between them and to external web-services (note: very advanced users only !).  This sample uses nginx to implement
  server side TLS.

## for orthanc developers
- [Orthanc integration tests](docker/orthanc-integration-tests) to demonstrate how to run the [Orthanc integration tests](https://bitbucket.org/sjodogne/orthanc-tests)

## for osimis/orthanc-pro image users

Note that the osimis/orthanc-pro images are private.  Access is restricted to companies who have subscribed a [support contract](https://www.osimis.io/en/services.html).

- [Orthanc on Azure](docker/azure) to demonstrate how to use the Orthanc in an Azure environment (using Azure SQL and Azure Blob Storage)
- [Orthanc on AWS](docker/aws) to demonstrate how to use the Orthanc in an AWS environment (using RDS and S3)
- [Orthanc on Google Cloud](docker/google-cloud-storage) to demonstrate how to use the Orthanc in an Google Cloud environment (using SQL Instance and Google Cloud Storage)
- [Orthanc + MSSQL](docker/mssql) to demonstrate how to use the Orthanc [MSSQL plugin](https://osimis.atlassian.net/wiki/spaces/OKB/pages/302743840/MSSQL+Index+plugin)
- [Object-storage plugins performance tests](docker/performance-tests) to compare performance of VM SSDs vs object-storage plugins


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

- [retry jobs](lua-samples/job-retries.py)
- [pydicom integration](docker/python/orthanc/test.py)
