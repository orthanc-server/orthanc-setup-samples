# Purpose

This is a sample setup to demonstrate how to interface Orthanc with
Dcm4Chee (version 5).

# Description

Docker Compose will start two main containers (`orthanc` for Orthanc,
and `arc` for Dcm4Chee). The network interfaces of those two main
containers are linked together. Note that two ancillary containers
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

* To start the setup, type: `$ docker-compose -p dcm4chee up`

* To stop the setup, type: `$ docker-compose -p dcm4chee down`

* If you need to send DICOM instances from Dcm4Chee to Orthanc
  (including for query/retrieve), you have to register Orthanc as a
  modality in Dcm4Chee [using the dedicated configuration
  interface](https://localhost:8443/dcm4chee-arc/ui2/device/aelist),
  as shown in this [screenshot](./dcm4chee-add-dicom.png). Note that
  the `orthanc` hostname is automatically assigned by Docker Compose.

# Using the DICOM protocol

* To **test connectivity using C-Echo** from Orthanc to Dcm4Chee:

```
$ curl http://localhost:8042/modalities/dcm4chee/echo -d '{}'
{}
```

* To **send using C-Store** a DICOM resource from Orthanc to Dcm4Chee
  (in this example, we are sending a DICOM study whose [Orthanc
  identifier](https://book.orthanc-server.com/faq/orthanc-ids.html) is
  `66c8e41e-ac3a9029-0b85e42a-8195ee0a-92c2e62e`):

```
$ curl http://localhost:8042/modalities/dcm4chee/store -d '{"Resources":["66c8e41e-ac3a9029-0b85e42a-8195ee0a-92c2e62e"]}'
```

* To **query** for all the studies stored by Dcm4chee (i.e. to make
  Orthanc issue a **C-Find** command to Dcm4Chee):

```
$ curl http://localhost:8042/modalities/dcm4chee/query -d '{"Level":"Study"}'
{
   "ID" : "4dc64a99-ec6a-48a8-bb8a-cf53caee4cc0",
   "Path" : "/queries/4dc64a99-ec6a-48a8-bb8a-cf53caee4cc0"
}
$ curl http://localhost:8042/queries/4dc64a99-ec6a-48a8-bb8a-cf53caee4cc0/answers?expand
[...]
```

* To **retrieve** the result of one query (i.e. to make Orthanc issue
  a **C-Move** command to Dcm4Chee), after having deleted the sample
  DICOM file from Orthanc:

```
$ curl http://localhost:8042/studies/66c8e41e-ac3a9029-0b85e42a-8195ee0a-92c2e62e -X DELETE
$ curl http://localhost:8042/studies/
[]
$ curl http://localhost:8042/queries/f50b51b4-4e60-4276-9bd3-c7f7a77bd996/retrieve -d '{}'
{
   "Description" : "REST API",
   "LocalAet" : "ORTHANC",
   "Query" : [
     ...
   ],
   "RemoteAet" : "DCM4CHEE"
}
$ curl http://localhost:8042/studies/
[ "66c8e41e-ac3a9029-0b85e42a-8195ee0a-92c2e62e" ]
```

* To **query** for all studies from a specific patient stored by Dcm4chee (i.e. to make
  Orthanc issue a **C-Find** command to Dcm4Chee):

```
$ curl http://localhost:8042/modalities/dcm4chee/query -d '{"Level":"Study", "Query": {"PatientID": "2345", "SopClassesInStudy": ""}}'
{
   "ID" : "4dc64a99-ec6a-48a8-bb8a-cf53caee4cc0",
   "Path" : "/queries/4dc64a99-ec6a-48a8-bb8a-cf53caee4cc0"
}
$ curl http://localhost:8042/queries/4dc64a99-ec6a-48a8-bb8a-cf53caee4cc0/answers?expand
[...]
```

* To **retrieve** the result of the query using **C-Get**

```
$ curl http://localhost:8042/queries/f50b51b4-4e60-4276-9bd3-c7f7a77bd996/get -d '{}'
```


* More examples about performing query/retrieve from Orthanc are
  available [in the Orthanc
  Book](https://book.orthanc-server.com/users/rest.html#performing-query-retrieve-c-find-and-find-with-rest).

# Using the DICOMweb protocol

* To **send using STOW-RS** a DICOM resource from Orthanc to Dcm4Chee
  (in this example, we are sending a DICOM study whose [Orthanc
  identifier](https://book.orthanc-server.com/faq/orthanc-ids.html) is
  `66c8e41e-ac3a9029-0b85e42a-8195ee0a-92c2e62e`):

```
$ curl http://localhost:8042/dicom-web/servers/dcm4chee/stow -d '{"Resources":["66c8e41e-ac3a9029-0b85e42a-8195ee0a-92c2e62e"]}'
{
   "InstancesCount" : "1",
   "NetworkSizeMB" : "0"
}
```

* To **query using QIDO-RS** the list of whole the DICOM studies
  stored in Dcm4Chee (the `/studies` URI is relative to the root of
  the DICOMweb server of Dcm4Chee):

```
$ curl http://localhost:8042/dicom-web/servers/dcm4chee/qido -d '{"Uri":"/studies"}'
```

* To **retrieve using WADO-RS** one specific DICOM study, whose `Study
  Instance UID (0008,1190)` tag is
  `1.2.840.113543.6.6.4.7.64067529866380271256212683512383713111129`:

```
$ curl http://localhost:8042/dicom-web/servers/dcm4chee/wado -d '{"Uri":"/studies/1.2.840.113543.6.6.4.7.64067529866380271256212683512383713111129"}'
```

* More examples about using the DICOMweb client of Orthanc are
  available [in the Orthanc
  Book](https://book.orthanc-server.com/plugins/dicomweb.html#rest-api-of-the-orthanc-dicomweb-client).

