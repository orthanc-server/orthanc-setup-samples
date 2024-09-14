# make sure to remove volumes
docker compose down -v
docker compose up -d

# might need to wait longer the first time !
sleep 10

curl http://localhost:8040/instances/ --data-binary @Study.zip > /dev/null
curl http://localhost:8043/instances/ --data-binary @Study.zip > /dev/null
curl http://localhost:8044/instances/ --data-binary @Study.zip > /dev/null


study_id=1.2.276.0.7230010.3.1.2.380373504.1.1597664635.911712

echo "######## BETA ##########"
port=8040
# two calls to analyze cache effect
time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
# QIDO-RS
time curl "http://localhost:$port/dicom-web/studies?PatientID=*&includefield=NumberOfStudyRelatedInstances" > /dev/null
time curl "http://localhost:$port/dicom-web/instances?PatientID=*" > /dev/null

echo "######## STABLE ##########"
port=8043
# two calls to analyze cache effect
time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
# QIDO-RS
time curl "http://localhost:$port/dicom-web/studies?PatientID=*&includefield=NumberOfStudyRelatedInstances" > /dev/null
time curl "http://localhost:$port/dicom-web/instances?PatientID=*" > /dev/null


echo "######## OLD ##########"
port=8044
# two calls to analyze cache effect
time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
time curl http://localhost:$port/dicom-web/studies/$study_id/metadata > /dev/null
# QIDO-RS
time curl "http://localhost:$port/dicom-web/studies?PatientID=*&includefield=NumberOfStudyRelatedInstances" > /dev/null
time curl "http://localhost:$port/dicom-web/instances?PatientID=*" > /dev/null

