#!/bin/bash
# sample usages:
#  upload files to port 4242 with 4 concurrent storscu:
# ./upload-files.sh 5042 9042 4

set -o errexit
set -o xtrace


rootfolder="/mnt/c/Users/Alain/o/dicom-files"

start=$(date +%s%N)
pids=""
result=0
concurrent_processes=${3:-1}
dicom_port=${1:-4242}
http_port=${2:-8042}

curl http://localhost:$http_port/changes?last

for i in `seq 1 $concurrent_processes`; do
    # storescu -xs --recurse --scan-directories -aec ORTHANC -aet STORESCU 127.0.0.1 $dicom_port "$rootfolder/store-scu/files/thorax-ct-1" &
    # python3 pynetdicom_upload.py --dicom_port=$dicom_port --folder="$rootfolder/store-scu/files/thorax-ct-1" &
    python3 http_upload.py --http_port=$http_port --folder="$rootfolder/store-scu/files/thorax-ct-1" &
    # ./curl-upload.sh "$rootfolder/store-scu/files/thorax-ct-1" $http_port &
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
