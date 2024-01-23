# Purpose

This is a sample setup to demonstrate how to combine Orthanc and [MedDream viewer](https://www.softneta.com/products/meddream-dicom-viewer/).
Unlike the other Meddream sample, here, the DICOMweb protocol is used by Meddream to query Orthanc.

Note that, Meddream being a commercial product, you'll need a license to run the demo completely.  However,
it is still accessible in evaluation mode with some annoying popups.

# Description

This demo contains:

- an Orthanc container with Orthanc Explorer 2 enabled.
- a MedDream container


# Starting the setup

To start the setup, type: `docker-compose up --build`.

# demo

- upload a study in [Orthanc UI](http://localhost:8042/ui/app/#/) (`demo/demo`)
- browse to this study and click 'Open in MedDream'
- you'll need to enter a MedDream login (`demo/demo` as well)
- you can also browse the studies through MedDream [broswing interface](http://localhost:8080)
