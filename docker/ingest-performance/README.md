
Foreword: 
- We've tested upload both with storescu and pynetdicom.  In all cases, storescu was 20-30% faster therefore, we used storescu for all our tests
- tests were performed with orthanc mainline and GDCM mainline (nov 11 2021) but a quick test with 21.10.0 leads to the same results.


Test with Orthanc storage on a SSD
----------------------------------

- source image is a CT with 373 slices in Little Endian Explicit (187MB) on a SSD
- source is on a SSD, orthanc-storage on SSD
- storescu and Orthanc are running on the same machine - 6 CPU - 12 cores

|                                                                    | single storescu | 2 storescu in // | 4 storescu in // | 8 storescu in // | 16storescu in // |
| ------------------------------------------------------------------ | --------------- | ---------------- | ---------------- | ---------------- | ---------------- |
| no ingest transcoding - DicomThreadsCount = 1                      |            27.7 |             24.5 |             26.8 |             30.5 |             60.4 |
| no ingest transcoding - DicomThreadsCount = 4                      |            25.9 |             25.1 |             25.1 |             25.6 |             37.5 |
| transcoding with DCMTK to JPEG lossless (.70) - DicomThreads = 4   |            28.3 |             27.3 |                  |             27.3 |             41.3 |
| transcoding with GDCM to JPEG lossless (.70) - DicomThreads = 4    |            28.8 |             27.4 |                  |             27.1 |             41.6 |

Performance is very poor with a single storescu (around 13 images/sec) but there's no impact of muliple concurrent connections:  with 8 concurrent connections,
we reach around 110 images/sec and even 145 images/sec with 16 concurrent connections.  We still need to understand why !  


now uploading files with http_upload.py:


|                                                                    | single client   | 2 clients in //  | 4 clients in //  | 8 clients in //  | 16 clients in // |
| ------------------------------------------------------------------ | --------------- | ---------------- | ---------------- | ---------------- | ---------------- |
| no ingest transcoding                                              |             6.8 |              7.1 |              8.8 |             18.0 |             38.4 |
| transcoding with DCMTK to JPEG lossless (.70)                      |             9.6 |              9.6 |             12.0 |             18.7 |             40.7 |
| transcoding with GDCM to JPEG lossless (.70)                       |             9.9 |              9.9 |             11.7 |             19.9 |             39.2 |
  


Test with Orthanc storage on a HDD
----------------------------------

- source image is a CT with 373 slices in Little Endian Explicit (187MB)
- source is on a SSD, orthanc-storage on USB2 HDD (very slow !)
- storescu and Orthanc are running on the same machine - 6 CPU - 12 cores
- to mount the USB disk under wsl:

```
sudo mkdir /mnt/usb-hdd
sudo mount -t drvfs d: /mnt/usb-hdd
```

|                                                              | single storescu | 2 storescu in // | 4 storescu in // | 8 storescu in // | 16storescu in // |
| ------------------------------------------------------------ | --------------- | ---------------- | ---------------- | ---------------- | ---------------- |
| no ingest transcoding - DicomThreadsCount = 1                |            89.5 |            168.8 |                  |                  |                  |
| no ingest transcoding - DicomThreadsCount = 4                |            91.5 |            128.8 |           261.7  |                  |                  |
