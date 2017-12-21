# Purpose

This is a sample setup to demonstrate how to share environment files between
multiple orthanc services.  I.e: have a single file that defines all
Dicom modalities and another file to share default settings.

We also demonstrate how one can override some settings from env_file by
providing custom env var in the `environment` section of the service (check for
the `NAME` of the `orthanc-c` service and for the `WVB_ENABLED` option)

# Description

This demo contains:

- 3 Orthanc instances (A, B, C) configured with DICOM connections enabled between them

# Starting the setup

To start the setup, type: `docker-compose up`

# demo

As described in the `docker-compose.yml` file, 

- Orthanc A is accessible on [http://localhost:8042](http://localhost:8042))
- Orthanc B is accessible on [http://localhost:8043](http://localhost:8043))
- Orthanc C is accessible on [http://localhost:8044](http://localhost:8044))

Once you've pushed some exams to an Orthanc instance, you can transfer it from one
to the other.

Check the name of each Orthanc instance.  The name of Orthanc C shall be different from
the other ones.  The Webviewer is enabled in Orthanc A & B but not in C since it has been
disabled in the `environment` section.