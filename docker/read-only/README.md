# Purpose

This is a sample setup to demonstrate how to run the `orthancteam/orthanc` image in read-only.

# Description

This demo contains:

- 2 Orthanc containers, one running in read-only mode and one running in normal mode.
- a PostgreSQL container to handle the Orthanc DB
- an nginx container that:
  - exposes the Orthanc UI on http://localhost/orthanc-read-only/ui/app/ and http://localhost/orthanc/ui/app/

# Starting the setup

To start the setup, type: `docker-compose up --build`
