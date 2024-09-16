# Purpose

This is a sample setup to demonstrate how to configure Orthanc with a PostgreSQL database and add latency between Orthanc and PG.

# Description

|   | Beta 2 |  24.8.3  | 22.3.0    |
|:---|---:|---:|---:|
|upload  | 9.379  |   14.260  | 15.443  |
|/metadata (1st call) (MainDicomTags mode)  |  4.124 |    6.459  | 11.052  |
|/metadata (2nd call) (MainDicomTags mode)  |  4.191 |    6.378   | 11.026  |
|/metadata (1st call) (Full mode)  |  13.562 |    22.362  | 9.640  |
|/metadata (2nd call) (Full mode)  |  0.090 |    0.123   | 9.619  |
|/studies?PatientID=* (1st call)   |  0.030 |   0.756   |  0.076 |
|/studies?PatientID=* (2nd call)  |  0.032 |   0.755   |  0.072 |
|/instances?PatientID=* (1st call) |  0.733 |   18.071   | 16.248  |
|/instances?PatientID=* (2nd call)  |  0.751 |   22.035   | 16.313  |