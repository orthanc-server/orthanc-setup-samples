Read-Write performance tests of object-storage plugins
======================================================

The aim of this setup is to compare the read/write performance of
object-storage vs VM SSDs in cloud environments

3 studies are used for tests with variations in the file size and numbers:

- MAMMO: 853 MB in 8 files
- CARDIO: 251 MB in 26 files
- ONCO: 356 MB in 1635 files

4 tasks are performed:

- upload the study with a single HTTP client
- upload the study with 10 HTTP clients in parallel
- download the study with a single HTTP client
- download the study with 10 HTTP clients in parallel

We also compare performance with raw disk performance:

- write 1 GB: `time dd if=/dev/zero of=file.1gb count=1024 bs=1048576`
- clear disk cache & read 1 GB:  `sync; echo 3 > /proc/sys/vm/drop_caches && time cat file.1gb > /dev/null`

Other remarks:

- All these tests have been performed with osimis/orthanc-pro:20.9.5 (Orthanc 1.7.3 + objects-storage 1.0.0)
- When not specified, the units in the tables are [seconds].
- We've not observed any significant differences when using SQLite vs PostgreSQL for the orthanc DB.  Therefore, all
  tests have been performed with SQLite.

To run the tests, you'll execute the python script on your VM.  Here are some sample command lines:

- `pip3 install -r requirements.txt`
- `python3 tester.py --orthancUrl http://localhost:8044 -u -dt -t 10`

AWS S3
------

Test results on an S3 EC2 instance Ubuntu 18.04 (t3a.large: 2 vCPUs - 8GB RAM).
Fast SSD is a 3000 IOPS with guaranteed throughput



|                                |                                |        fast SSD |              S3 |            diff |
| ------------------------------ | ------------------------------ | --------------- | --------------- | --------------- |
|           raw disk performance |                     write 1 GB |           0.571 |              NA |              NA |
|                                |                      read 1 GB |           2.790 |              NA |              NA |
|                                |                                |                 |                 |                 |
|                upload 1 client |                          MAMMO |           3.861 |          14.178 |          +267 % |
|                                |                         CARDIO |           1.050 |           7.195 |          +585 % |
|                                |                           ONCO |           8.564 |         184.624 |         +2055 % |
|                                |                                |                 |                 |                 |
|              upload 10 clients |                          MAMMO |           2.863 |           6.460 |          +125 % |
|                                |                         CARDIO |           0.771 |           1.678 |          +117 % |
|                                |                           ONCO |           6.234 |          23.799 |          +281 % |
|                                |                                |                 |                 |                 |
|              download 1 client |                          MAMMO |          25.741 |          38.256 |           +48 % |
|                                |                         CARDIO |          15.450 |          19.280 |           +24 % |
|                                |                           ONCO |          37.386 |         108.078 |          +189 % |
|                                |                                |                 |                 |                 |
|            download 10 clients |                          MAMMO |          18.330 |          20.424 |           +11 % |
|                                |                         CARDIO |          10.485 |          11.374 |            +8 % |
|                                |                           ONCO |          26.209 |          29.116 |           +11 % |
|                                |                                |                 |                 |                 |



Azure blob storage
------------------

Test results on an Azure instance running Ubuntu 18.04 (Standard_D2s_v3: 2 vCPUs - 8GB RAM).
SSD is a Premium SSD with 2300 IOPS and a max throughput of 150 MBps

Note that the SSD performances are not repeatable at all across test repetitions.  This might be due to the fact that
we used a "dev" subscription in which performances are not guaranteed.  Feel free to run these tests on your prod
environment.

|                                |                                |        fast SSD |           Azure |            diff |
| ------------------------------ | ------------------------------ | --------------- | --------------- | --------------- |
|           raw disk performance |                     write 1 GB |           3.952 |              NA |              NA |
|                                |                      read 1 GB |          27.094 |              NA |              NA |
|                                |                                |                 |                 |                 |
|                upload 1 client |                          MAMMO |           7.189 |          36.061 |           +401% |
|                                |                         CARDIO |           1.133 |           7.222 |           +537% |
|                                |                           ONCO |           9.910 |         127.502 |          +1186% |
|                                |                                |                 |                 |                 |
|              upload 10 clients |                          MAMMO |          18.043 |          15.231 |            -16% |
|                                |                         CARDIO |          10.518 |           3.512 |            -66% |
|                                |                           ONCO |          13.384 |          18.960 |            +41% |
|                                |                                |                 |                 |                 |
|              download 1 client |                          MAMMO |          41.666 |          34.967 |            -16% |
|                                |                         CARDIO |          14.275 |          18.859 |            +32% |
|                                |                           ONCO |          73.055 |          65.122 |            -11% |
|                                |                                |                 |                 |                 |
|            download 10 clients |                          MAMMO |          18.043 |          22.423 |            +24% |
|                                |                         CARDIO |          11.852 |          12.490 |             +5% |
|                                |                           ONCO |          26.869 |          28.068 |             +4% |
|                                |                                |                 |                 |                 |


Conclusions
-----------

* Writing on SSD is much faster than reading.  This can be explained by disk caching.  This write cache gives a clear 
  advantage to SSD compared to object storage.

* Since the aim of this test is to test the Orthanc read/write performance, the source images are stored on the VM SSDs of the machine running Orthanc (same for downloaded files that are stored on the VM SSDs too).  This is actually not representative of a real setup in which source files would most likely come from a web interface at a much lower speed and where files downloaded from Orthanc would be sent to an HTTP client that has requested them also through a much slower web interface.  Therefore, although the differences seems huge in these tests, it will most likely appear neglectible in an end-to-end test between a remote HTTP client.  I.e, on my home PC with a 75 Mbps download speed and 4.2 Mbps upload speed, we get:

|                                |                                |        fast SSD |              S3 |            diff |
| ------------------------------ | ------------------------------ | --------------- | --------------- | --------------- |
|                                |                                |                 |                 |                 |
|                upload 1 client |                         CARDIO |           494.3 |           495.6 |            ~0 % |
|                                |                                |                 |                 |                 |
|              upload 10 clients |                         CARDIO |           494.9 |           495.3 |            ~0 % |
|                                |                                |                 |                 |                 |
|              download 1 client |                         CARDIO |            42.2 |            46.0 |            +9 % |
|                                |                                |                 |                 |                 |
|            download 10 clients |                         CARDIO |            28.8 |            31.6 |            +9 % |
|                                |                                |                 |                 |                 |

* As expected, the object-storage are well suited for multiple concurrent connections.  However, we've observed that, beyond 4-5 concurrent 
HTTP clients, the performance does not scale anymore (both with AWS and Azure).  This still needs to be explained/investigated !

|                                |                                |           Azure |
| ------------------------------ | ------------------------------ | --------------- |
|                                |                                |                 |
|              download 1 client |                           ONCO |            78.0 |
|             download 2 clients |                           ONCO |            38.8 |
|             download 3 clients |                           ONCO |            32.0 |
|             download 4 clients |                           ONCO |            29.8 |
|             download 5 clients |                           ONCO |            28.7 |
|            download 10 clients |                           ONCO |            27.8 |