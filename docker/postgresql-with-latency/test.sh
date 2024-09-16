# make sure to remove volumes
docker compose down -v
docker compose up -d

# might need to wait longer the first time !
sleep 10

# time curl http://localhost:8040/instances/ --data-binary @Study.zip > /dev/null
# time curl http://localhost:8043/instances/ --data-binary @Study.zip > /dev/null
# time curl http://localhost:8044/instances/ --data-binary @Study.zip > /dev/null


study_id=1.2.276.0.7230010.3.1.2.380373504.1.1597664635.911712

test() {
    port=$1

    echo "upload"
    time curl http://localhost:$port/instances/ --data-binary @Study.zip > /dev/null

    # two calls to analyze cache effect
    echo "first call to /metadata"
    time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
    echo "second call to /metadata"
    time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
    # QIDO-RS
    echo "first call to /studies?PatientID="
    time curl "http://localhost:$port/dicom-web/studies?PatientID=*&includefield=NumberOfStudyRelatedInstances" > /dev/null
    echo "second call to /studies?PatientID="
    time curl "http://localhost:$port/dicom-web/studies?PatientID=*&includefield=NumberOfStudyRelatedInstances" > /dev/null
    echo "first call to /instances?PatientID="
    time curl "http://localhost:$port/dicom-web/instances?PatientID=*" > /dev/null
    echo "second call to /instances?PatientID="
    time curl "http://localhost:$port/dicom-web/instances?PatientID=*" > /dev/null
}

echo "######## BETA ##########"
test 8040

echo "######## STABLE ##########"
test 8043

echo "######## OLD ##########"
test 8044

