# sample usages:
#  upload files to port 4242 with 4 concurrent storscu:
# ./upload-files.sh 9042 9042 4

set -o errexit
set -o xtrace

folder=$1
http_port=${2:-8042}

for i in $folder/**/*; 
    do [ -f "$i" ] && curl -X POST http://localhost:$http_port/instances --data-binary @"$i"; 
    done
