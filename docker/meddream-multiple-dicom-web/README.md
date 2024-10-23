# Purpose

This is a sample setup to demonstrate how to combine Orthanc and [MedDream viewer](https://www.softneta.com/products/meddream-dicom-viewer/).
Unlike the other Meddream sample, here, the DICOMweb protocol is used by Meddream to query Orthanc and a single MedDream server is connected to
multiple Orthanc instances.

Note that, Meddream being a commercial product, you'll need a license to run the demo completely.  However,
it is still accessible in evaluation mode with some annoying popups.

# Description

This demo contains:

- 2 Orthanc containers with Orthanc Explorer 2 enabled.
- a MedDream container
- a MedDream token service container that generates tokens to grant access to specific resources

Note: the token-service is enabled in MedDream which means that the MedDream buttons won't work in OE2.

# Starting the setup

To start the setup, type: `docker-compose up --build`.

# demo

- upload a study in [Orthanc A UI](http://localhost:8044/ui/app/#/) (`demo/demo`)
- upload another study in [Orthanc B UI](http://localhost:8045/ui/app/#/) (`demo/demo`)


To generate a token to access a study:

```
curl http://token-user:change-me@localhost:8088/v3/generate -H "Content-Type: application/json" --data '{"items": [{"studies": { "study": "1.2.3.4.5", "storage": "orthanc-a"}}]}'
```

And then, open http://localhost:8080/?study=1.2.3.4.5&token=token-value

```
Real examples:

curl http://token-user:change-me@localhost:8088/v3/generate -H "Content-Type: application/json" --data '{"items": [{"studies": { "study": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058363.6979", "storage": "orthanc-b"}}]}'

http://localhost:8080/?study=1.2.276.0.7230010.3.1.2.2344313775.14992.1458058363.6979&token=ZqT-rFL3Uyr1rUTvW9RI0cvXe3ZWZB4xD65bP4EOZ73iay58esZ-gQNXJfWowPxoGEyj301MOb6kmPF-sCksNLhGfdcUR_4hOeOKBijbF6MUxt9cRSLQLwEaJ0o=

```