# Purpose

This is a sample setup to demonstrate how to run the [Orthanc integration tests](https://bitbucket.org/sjodogne/orthanc-tests/src) with a custom version of Orthanc.

# Description

This demo contains:

- an Orthanc container that you want to test (orthanc-under-tests).
- an Orthanc container with the Orthanc integration tests (orthanc-tests)

# Starting the setup

To start the setup, type: `docker-compose up --build --exit-code-from orthanc-tests --abort-on-container-exit`
