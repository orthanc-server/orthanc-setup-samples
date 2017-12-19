# Orthanc Setup samples

This repository contains sample Orthanc configurations to demonstrate how it can be configured in many use cases.  Right now, most of these samples use Docker to deploy Orthanc.

# Docker setups

These sample setups require Docker to run.  They have been tested only on Linux systems.  To test one of these setups, clone this repository and check the readme file in each sample folder.

## Getting started
- [Basic Orthanc](docker/basic) to demonstrate a very basic Orthanc setup.
- [Orthanc + PostgreSQL](docker/postgresql) to demonstrate how to use the Orthanc [PostgreSQL plugin](http://book.orthanc-server.com/plugins/postgresql.html)
- [Orthanc basic DICOM association](docker/dicom-association) to demonstrate a simple DICOM association between Orthanc servers (and perform operations such as C-FIND, C-MOVE, C-STORE, C-ECHO).
- [Orthanc peering](docker/peering) ([easy variant](docker/peering-easy)) to demonstrate Orthanc peering.
- [Orthanc basic HTTP authentication](docker/basic-authentication) to demonstrate static, basic HTTP authentication.
- [Orthanc AET check](docker/aet-check) to demonstrate called AET checking.
- [Sharing Orthanc configurations](docker/share-docker-compose-env-file) to demonstrate how to share configuration settings between multiple instance of Orthanc in the same Docker network.

## for advanced users
- [Orthanc transcode middleman](docker/transcode-middleman) to demonstrate how to use Orthanc to change the TransferSyntax of instances inbetween a modality and a PACS.
- [Implementing HTTPS with nginx](docker/tls-with-nginx) to demonstrate how to implement and Orthanc behind a reverse proxy.

## for experts
- [Enable Osimis WebViewer Liveshare](docker/webviewer-pro+liveshare) to demonstrate how to use Osimis WebViewer pro plugin and enable its Liveshare feature.


## for software integrators
- [Orthanc + Serve-Folders Plugin](docker/serve-folders) to demonstrate how to use the Orthanc [Serve-Folders plugin](http://book.orthanc-server.com/plugins/serve-folders.html) to build custom web interface on top of Orthanc
- [Orthanc + Authorization Plugin](docker/authorization-plugin) to demonstrate how to use the Orthanc [authorization plugin](http://book.orthanc-server.com/plugins/authorization.html)
- [Orthanc mutual TLS authentication](docker/full-tls) to demonstrate how to use client certificates to authentify Orthanc instances between them and to external web-services (note: very advanced users only !).
