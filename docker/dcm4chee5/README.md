# Purpose

This is a sample setup to demonstrate how to interface Orthanc with
Dcm4Chee (version 5).

# Description

Docker Compose will start two main containers (`orthanc` for Orthanc,
and `arc` for Dcm4Chee). The network interfaces of those two main
containers are linked together. Note that two ancilliary containers
internal to Dcm4Chee will also be started (namely `ldap` and `db`).

The Dcm4Chee setup directly derives from the "Run minimum set of
archive services on a single host" [sample Docker Compose
configuration](https://github.com/dcm4che/dcm4chee-arc-light/wiki/Run-minimum-set-of-archive-services-on-a-single-host#use-docker-compose). Dcm4Chee
will store its data in the persistent `/tmp/dcm4chee-arc` folder.

The Orthanc setup comes from the [Orthanc
Book](https://book.orthanc-server.com/users/docker.html#configuration-management-using-docker-compose).
The whole configuration of Orthanc can be found in the
[orthanc.json](orthanc.json) file. Orthanc will store its data in the
persistent `/tmp/orthanc-storage` folder.

As this setup is minimal, HTTPS security is not enabled, which
explains why the `HttpsVerifyPeers` configuration option of Orthanc
has to be set to `false`.

# Using the setup

* To start the setup, type: `$ docker-compose -p dcm4chee up`.

* To stop the setup, type: `$ docker-compose -p dcm4chee down`.

# Using the DICOM protocol

* To issue a C-Echo command from Orthanc to Dcm4Chee:

    ```curl -u orthanc:orthanc http://localhost:8042/modalities/dcm4chee/echo -d '{}'```
