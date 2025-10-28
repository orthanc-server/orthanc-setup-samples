This is a sample setup to demonstrate how you can filter out some instances when
a C-Move is performed.
The instances are filtered based on the SOPClass.

# Description

This demo contains:

- an Orthanc container `orthanc` acting as a PACS.  This container has a custom python plugin
  to handle the C-Move queries and filter out the instances based on the defined filter.
- another Orthanc container `modality` acting as a modality that is querying studies from the PACS.


# Running the demo

First start setup with this command:

```
docker compose pull
docker compose up -d --force-recreate
```

Test scenario:
- reach first Orthanc (PACS) on `http://localhost:8042`
- upload both DICOM files from the `samples` folder
- reach second Orthanc (Modality) on `http://localhost:8043`
- from the `DICOM Modalities` page, query the PACS (fill `PatientID` field with `*`)
- click on the only study in the list and click on the `retrieve` button
- browse the list of studies (`All local studies` page) and click on the only study in the list
- As you can see, there is only one instance, the second instance (SOPClassUID: `1.2.840.10008.5.1.4.1.1.104.1`) has been filtered out!