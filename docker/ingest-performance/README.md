
Foreword: 

- We've tested upload both with storescu and pynetdicom.  In all cases, storescu was 20-30% faster therefore, we used storescu for all our tests
- tests were performed with orthanc mainline and GDCM mainline (nov 11 2021) but a quick test with 21.10.0 leads to the same results.



Test with Orthanc storage on a SSD - storescu
---------------------------------------------

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



Test with Orthanc storage on a SSD - HTTP client
------------------------------------------------

Same setup as SSD-storescu but uploading files with a python HTTP client in `http_upload.py`:


|                                                                    | single client   | 2 clients in //  | 4 clients in //  | 8 clients in //  | 16 clients in // |
| ------------------------------------------------------------------ | --------------- | ---------------- | ---------------- | ---------------- | ---------------- |
| no ingest transcoding                                              |             6.8 |              7.1 |              8.8 |             18.0 |             38.4 |
| transcoding with DCMTK to JPEG lossless (.70)                      |             9.6 |              9.6 |             12.0 |             18.7 |             40.7 |
| transcoding with GDCM to JPEG lossless (.70)                       |             9.9 |              9.9 |             11.7 |             19.9 |             39.2 |
  


Test with Orthanc storage on a HDD - storescu
---------------------------------------------

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





Detailed analisys of DICOM logs:
-------------------------------

```
orthanc-ssd_1        | I1110 11:40:45.073515 ServerContext.cpp:624] New instance stored
--> 11ms lost by storescu between 2 instances ?
orthanc-ssd_1        | T1110 11:40:45.084063 CommandDispatcher.cpp:757] (dicom) Received Command:
orthanc-ssd_1        | ===================== INCOMING DIMSE MESSAGE ====================
orthanc-ssd_1        | Message Type                  : C-STORE RQ
orthanc-ssd_1        | Presentation Context ID       : 43
orthanc-ssd_1        | Message ID                    : 368
orthanc-ssd_1        | Affected SOP Class UID        : CTImageStorage
orthanc-ssd_1        | Affected SOP Instance UID     : 1.2.276.0.7230010.3.1.4.313263104.1.1536143728.617415
orthanc-ssd_1        | Data Set                      : present
orthanc-ssd_1        | Priority                      : medium
orthanc-ssd_1        | ======================= END DIMSE MESSAGE =======================
orthanc-ssd_1        | I1110 11:40:45.084120 main.cpp:352] Incoming Store request from AET STORESCU on IP 192.168.96.1, calling AET ORTHANC
--> 60ms to receive data (compared to 11ms in HTTP !)
orthanc-ssd_1        | T1110 11:40:45.141900 OrthancPlugins.cpp:5186] (plugins) Calling service 38 from plugin /usr/share/orthanc/plugins/libOrthancGdcm.so
orthanc-ssd_1        | I1110 11:40:45.143408 FilesystemStorage.cpp:124] Creating attachment "285b89df-1d0b-4cac-ac0f-9a206640b2c8" of "DICOM" type (size: 1MB)
orthanc-ssd_1        | I1110 11:40:45.148557 StatelessDatabaseOperations.cpp:3024] Overwriting instance: f626cc11-109c30d0-c200eb48-4e2934e6-04cb56e8
orthanc-ssd_1        | T1110 11:40:45.149801 ServerIndex.cpp:141] Remaining ancestor "a9c10850-fe5e33cb-edc73fd8-44293d8e-23cec1da" (3)
orthanc-ssd_1        | T1110 11:40:45.149841 ServerIndex.cpp:174] Change related to resource f626cc11-109c30d0-c200eb48-4e2934e6-04cb56e8 of type Instance: Deleted
orthanc-ssd_1        | T1110 11:40:45.150264 ServerIndex.cpp:174] Change related to resource f626cc11-109c30d0-c200eb48-4e2934e6-04cb56e8 of type Instance: NewInstance
--> new instance change is slower than others: 2ms (observed everytime)
orthanc-ssd_1        | T1110 11:40:45.152060 ServerIndex.cpp:174] Change related to resource a9c10850-fe5e33cb-edc73fd8-44293d8e-23cec1da of type Series: NewChildInstance
orthanc-ssd_1        | T1110 11:40:45.152092 ServerIndex.cpp:174] Change related to resource 48208f7a-e436dfef-9d2a1d04-d3a35ceb-94e16ea6 of type Study: NewChildInstance
orthanc-ssd_1        | T1110 11:40:45.152099 ServerIndex.cpp:174] Change related to resource 17f271d7-b6afebbe-025749a1-05a6c214-02013c4d of type Patient: NewChildInstance
orthanc-ssd_1        | I1110 11:40:45.152998 FilesystemStorage.cpp:258] Deleting attachment "4532f102-b446-4a0a-8c41-5ecfcf579917" of type 1
orthanc-ssd_1        | I1110 11:40:45.153168 ServerContext.cpp:624] New instance stored
orthanc-ssd_1        | T1110 11:40:45.163888 CommandDispatcher.cpp:757] (dicom) Received Command:
```



Detailed analisys of http client logs:
-------------------------------------

```
orthanc-ssd_1        | T1110 11:48:06.401256 HttpServer.cpp:1162] (http) HTTP header: [content-length]: [526018]
--> no time lost between 2 instances like we observed with storescu
orthanc-ssd_1        | I1110 11:48:06.401264 HttpServer.cpp:1238] (http) POST /instances
orthanc-ssd_1        | I1110 11:48:06.403291 OrthancRestApi.cpp:173] (http) Receiving a DICOM file of 526018 bytes through HTTP
--> 10 ms to receive the file and start transcoding it
--> only 1 ms to transcode !!
orthanc-ssd_1        | T1110 11:48:06.411850 OrthancPlugins.cpp:5186] (plugins) Calling service 38 from plugin /usr/share/orthanc/plugins/libOrthancGdcm.so
orthanc-ssd_1        | I1110 11:48:06.412929 FilesystemStorage.cpp:124] Creating attachment "71a42b33-cd54-4c7d-9750-959e6dc52094" of "DICOM" type (size: 1MB)
orthanc-ssd_1        | I1110 11:48:06.415969 StatelessDatabaseOperations.cpp:3024] Overwriting instance: 69a4cc9d-262168ad-3c1e8ca1-868ddd3e-02a7901c
orthanc-ssd_1        | T1110 11:48:06.416939 ServerIndex.cpp:141] Remaining ancestor "a9c10850-fe5e33cb-edc73fd8-44293d8e-23cec1da" (3)
orthanc-ssd_1        | T1110 11:48:06.416976 ServerIndex.cpp:174] Change related to resource 69a4cc9d-262168ad-3c1e8ca1-868ddd3e-02a7901c of type Instance: Deleted
orthanc-ssd_1        | T1110 11:48:06.417416 ServerIndex.cpp:174] Change related to resource 69a4cc9d-262168ad-3c1e8ca1-868ddd3e-02a7901c of type Instance: NewInstance
--> new instance change is slower than others: 2ms (observed everytime)
orthanc-ssd_1        | T1110 11:48:06.419635 ServerIndex.cpp:174] Change related to resource a9c10850-fe5e33cb-edc73fd8-44293d8e-23cec1da of type Series: NewChildInstance
orthanc-ssd_1        | T1110 11:48:06.419670 ServerIndex.cpp:174] Change related to resource 48208f7a-e436dfef-9d2a1d04-d3a35ceb-94e16ea6 of type Study: NewChildInstance
orthanc-ssd_1        | T1110 11:48:06.419677 ServerIndex.cpp:174] Change related to resource 17f271d7-b6afebbe-025749a1-05a6c214-02013c4d of type Patient: NewChildInstance
orthanc-ssd_1        | I1110 11:48:06.420601 FilesystemStorage.cpp:258] Deleting attachment "13700143-9cf3-4f65-818b-9aa2a80cd348" of type 1
orthanc-ssd_1        | I1110 11:48:06.420774 ServerContext.cpp:624] New instance stored
orthanc-ssd_1        | T1110 11:48:06.421314 HttpOutput.cpp:474] Compressing a HTTP answer using gzip
--> 7ms to compress the answer that is just a few hundreds of bytes ???
orthanc-ssd_1        | T1110 11:48:06.428200 HttpServer.cpp:1162] (http) HTTP header: [host]: [localhost:9042]
orthanc-ssd_1        | T1110 11:48:06.428244 HttpServer.cpp:1162] (http) HTTP header: [user-agent]: [python-requests/2.22.0]
orthanc-ssd_1        | T1110 11:48:06.428252 HttpServer.cpp:1162] (http) HTTP header: [accept-encoding]: [gzip, deflate]
orthanc-ssd_1        | T1110 11:48:06.428257 HttpServer.cpp:1162] (http) HTTP header: [accept]: [*/*]
orthanc-ssd_1        | T1110 11:48:06.428263 HttpServer.cpp:1162] (http) HTTP header: [connection]: [keep-alive]
orthanc-ssd_1        | T1110 11:48:06.428269 HttpServer.cpp:1162] (http) HTTP header: [content-length]: [526018]
orthanc-ssd_1        | I1110 11:48:06.428277 HttpServer.cpp:1238] (http) POST /instances
orthanc-ssd_1        | I1110 11:48:06.430627 OrthancRestApi.cpp:173] (http) Receiving a DICOM file of 526018 bytes through HTTP

```

