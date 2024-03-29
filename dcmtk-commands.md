This file contains common DCMTK commands.  You can test them with the `test-dcmtk-commands` docker-compose setup in this repo.

FIND-SCU
========


Very basic C-Find query at study level to return all studies
```
findscu -v -d -k 0008,0052="STUDY" -k 0008,0020="" -k 0020,000D="" -S -aet FINDSCU -aec ORTHANC 127.0.0.1 104
```

Worklist Find SCU, searching for all scheduled CT for a given date
```
findscu -v -W -k "ScheduledProcedureStepSequence[0].Modality=CT" 127.0.0.1 4242
```


MOVE-SCU
========

Move 2 studies from ORTHANC to ORTHANCB
```
movescu -S -aec ORTHANC -aet MOVESCU -aem ORTHANCB -k "0008,0052=STUDY" -k "0020,000d=1.2.3.4\2.4.6.8" 127.0.0.1 104
```


STORE-SCU
=========

Upload a JPEG-LS folder to Orthanc

```
storescu -xs  -aec ORTHANC -aet STORESCU 127.0.0.1 4242 *
```