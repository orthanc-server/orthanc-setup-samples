#!/bin/bash
# sample usages:
#  upload files to port 4242 with 4 concurrent storscu:
# ./upload-files.sh 5042 9042 storescu 4

set -o errexit
set -o xtrace


rootfolder="/mnt/c/Users/Alain/o/dicom-files"


pids=""
result=0
mode=${3:-storescu}
concurrent_processes=${4:-1}
dicom_port=${1:-4242}
http_port=${2:-8042}

study_id=1.2.276.0.7230010.3.1.2.313263104.1.1536143728.617408

curl http://localhost:$http_port/changes?last

if [ "$mode" == "orthanc-source" ]; then
    # first upload to orthanc-source
    python3 http_upload.py --http_port=9044 --folder="$rootfolder/store-scu/files/thorax-ct-1"
fi

start=$(date +%s%N)

for i in `seq 1 $concurrent_processes`; do
    if [ "$mode" == "storescu" ]; then
        storescu -xs --recurse --scan-directories -aec ORTHANC -aet STORESCU 127.0.0.1 $dicom_port "$rootfolder/store-scu/files/thorax-ct-1" &
    elif [ "$mode" == "pynetdicom" ]; then
        python3 pynetdicom_upload.py --dicom_port=$dicom_port --folder="$rootfolder/store-scu/files/thorax-ct-1" &
    elif [ "$mode" == "http" ]; then
        python3 http_upload.py --http_port=$http_port --folder="$rootfolder/store-scu/files/thorax-ct-1" &
    elif [ "$mode" == "curl" ]; then
        ./curl-upload.sh "$rootfolder/store-scu/files/thorax-ct-1" $http_port &
    elif [[ "$mode" == orthanc* ]]; then    # use "orthanc" if data has already been uploaded to the source, "orthanc-source" otherwise
        movescu -S -aec ORTHANC-SOURCE -aet MOVESCU -aem ORTHANC-SSD -k "0008,0052=STUDY" -k "0020,000d=$study_id" 127.0.0.1 5044 &
    fi
    pids="$pids $!"
done

for pid in $pids; do
    wait $pid || let "result=1"
done

if [ "$result" == "1" ]; then
    exit 1
fi

end=$(date +%s%N)

curl http://localhost:$http_port/changes?last

echo "Elapsed time: $(($(($end-$start))/1000000)) ms"
