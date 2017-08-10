# Orthanc Setup samples

This repository contains sample Orthanc configurations to demonstrate how it can be configured in many use cases.  Right now, most of these samples use Docker to deploy Orthanc.

# Docker setups

These sample setups require Docker to run.  They have been tested only on Linux systems.  To test one of these setups, clone this repository and check the readme file in each sample folder.

- [Orthanc + PostgreSQL](docker/postgresql/README.md) to demonstrate how to use the Orthanc [PostgreSQL plugin](http://book.orthanc-server.com/plugins/postgresql.html)
- [Orthanc + Authorization Plugin](docker/authorization-plugin/README.md) to demonstrate how to use the Orthanc [authorization plugin](http://book.orthanc-server.com/plugins/authorization.html)
- [Orthanc transcode middleman](docker/transcode-middleman/README.md) to demonstrate how to use Orthanc to change the TransferSyntax of instances inbetween a modality and a PACS.
- [Orthanc mutual TLS authentication](docker/full-tls/README.md) to demonstrate how to use client certificates to authentify Orthanc instances between them and to external web-services (note: very advanced users only !).
- [Orthanc basic DICOM association](docker/dicom-association/README.md) to demonstrate a simple DICOM association between Orthanc servers (and perform operations such as C-FIND, C-MOVE, C-STORE, C-ECHO).
- [Orthanc peering](docker/peering/README.md) to demonstrate Orthanc peering.
