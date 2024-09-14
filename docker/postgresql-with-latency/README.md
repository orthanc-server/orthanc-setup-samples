# Purpose

This is a sample setup to demonstrate how to configure Orthanc with a PostgreSQL database and add latency between Orthanc and PG.

# Description

|   | Beta 1 | 24.8.3  | 22.3.0    |
|:---|---:|---:|---:|
|/metadata (1st call) (Metadata) mode  |  4.069 |  6.459  | 11.052  |
|/metadata (2nd call) (Metadata) mode  |  4.096 |  6.378   | 11.026  |
|/metadata (1st call) (Full) mode  |  16.985|  22.362  | 9.640  |
|/metadata (2nd call) (Full) mode  |  0.095 |  0.123   | 9.619  |
|/studies?PatientID=*   |  0.026 |  0.712   |  0.076 |
|/instances?PatientID=*   | 0.684  |  18.071   | 16.248  |