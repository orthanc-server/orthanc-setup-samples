# Orthanc Setup samples

This repository contains sample Orthanc configurations to demonstrate how it can be configured in many use cases.  Right now, most of these samples use Docker to deploy Orthanc.

# Docker setups

These sample setups require Docker to run.  They have been tested only on Linux systems.  To test one of these setups, clone this repository and check the readme file in each sample folder.

- [orthanc + postgresql](docker/orthanc+postgresql/README.md) to demonstrate how to use the Orthanc [PostgreSQL plugin](http://book.orthanc-server.com/plugins/postgresql.html)
- [orthanc + authorization plugin](docker/orthanc+authorization-plugin/README.md) to demonstrate how to use the Orthanc [authorization plugin](http://book.orthanc-server.com/plugins/authorization.html)
- [orthanc transcode middleman](docker/orthanc-transcode-middleman/README.md) to demonstrate how to use Orthanc to change the TransferSyntax of instances inbetween a modality and a PACS.