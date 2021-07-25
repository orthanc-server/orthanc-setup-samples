This file contains common DCMTK commands.  You can test them with the `test-dcmtk-commands` docker-compose setup in this repo.

FIND-SCU
========


Very basic C-Find query at study level to return all studies
```
findscu -v -d -k 0008,0052="STUDY" -k 0008,0020="" -k 0020,000D="" -S -aet FINDSCU -aec ORTHANC 127.0.0.1 104
```


MOVE-SCU
========

Move 2 studies from ORTHANC to ORTHANCB
```
movescu -S -aec ORTHANC -aet MOVESCU -aem ORTHANCB -k "0008,0052=STUDY" -k "1.2.3.4\2.4.6.8" 127.0.0.1 104
```