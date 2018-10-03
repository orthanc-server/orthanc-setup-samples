# Orthanc Setup samples

This repository contains sample Orthanc configurations to demonstrate how it can be configured in many use cases.  Right now, most of these samples use Docker to deploy Orthanc.

# Docker setups

These sample setups require Docker to run.  They have been tested only on Linux systems.  To test one of these setups, clone this repository and check the readme file in each sample folder.

## Getting started
- [Basic Orthanc](docker/basic) to demonstrate a very basic Orthanc setup.
- [Orthanc + PostgreSQL](docker/postgresql) to demonstrate how to use the Orthanc [PostgreSQL plugin](http://book.orthanc-server.com/plugins/postgresql.html)
- [Orthanc + MySQL](docker/mysql-easy) to demonstrate how to use the Orthanc [MySQL plugin](http://book.orthanc-server.com/plugins/mysql.html)
- [Orthanc basic DICOM association](docker/dicom-association) to demonstrate a simple DICOM association between Orthanc servers (and perform operations such as C-FIND, C-MOVE, C-STORE, C-ECHO).
- [Orthanc peering](docker/peering) ([easy variant](docker/peering-easy)) to demonstrate Orthanc peering.
- [Orthanc dicom-web](docker/dicom-web) to demonstrate Orthanc dicom-web connectivity.
- [Orthanc basic HTTP authentication](docker/basic-authentication) to demonstrate static, basic HTTP authentication.
- [Orthanc AET check](docker/aet-check) to demonstrate called AET checking.
- [Sharing Orthanc configurations](docker/share-docker-compose-env-file) to demonstrate how to share configuration settings between multiple instance of Orthanc in the same Docker network.

## for advanced users
- [C-Find requests filtering](docker/dicom-cfind-filter-lua) to demonstrate how you can modify C-Find requests in a lua script.
- [Orthanc transcode middleman](docker/transcode-middleman) to demonstrate how to use Orthanc to change the TransferSyntax of instances inbetween a modality and a PACS.
- [Implementing HTTPS with nginx](docker/tls-with-nginx) to demonstrate how to implement an Orthanc behind a reverse proxy.
- [Use multiple Orthanc on the same DB](docker/multiple-orthancs-on-same-db) to demonstrate how to connect multiple Orthanc on the same PostgreSQL database and perform HTTP load balancing.

## for commercial plugins users 
- [Enable Osimis WebViewer Liveshare](docker/webviewer-pro+liveshare) to demonstrate how to use Osimis WebViewer pro plugin and enable its Liveshare feature.
- [Orthanc + MSSQL](docker/mssql) to demonstrate how to use the Orthanc [MSSQL plugin](https://osimis.atlassian.net/wiki/spaces/OKB/pages/302743840/MSSQL+Index+plugin)


## for software integrators
- [Orthanc + Serve-Folders Plugin](docker/serve-folders) to demonstrate how to use the Orthanc [Serve-Folders plugin](http://book.orthanc-server.com/plugins/serve-folders.html) to build custom web interface on top of Orthanc
- [Orthanc + Authorization Plugin](docker/authorization-plugin) to demonstrate how to use the Orthanc [authorization plugin](http://book.orthanc-server.com/plugins/authorization.html)
- [Orthanc mutual TLS authentication](docker/full-tls) to demonstrate how to use client certificates to authentify Orthanc instances between them and to external web-services (note: very advanced users only !).

## for orthanc developers
- [Orthanc integration tests](docker/orthanc-integration-tests) to demonstrate how to run the [Orthanc integration tests](https://bitbucket.org/sjodogne/orthanc-tests)