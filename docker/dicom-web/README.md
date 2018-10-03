To start, use `docker-compose up --build -d`.
To stop, use `docker-compose down`.

# demo

- Connect to the orthanc 'foo' on [http://localhost:80](http://localhost:80).
- Upload an image to this instance of Orthanc.
- in a shell get the Orthanc ID of the study to transfer
```
curl http://localhost/studies
```
 This should reply something like this :
[ "ad5040ea-f640e840-9c9351be-4608e36e-7f5e8894" ]
- send the study to the second Orthanc (replace the study ID by the one receveid just above)
```
curl http://localhost:80/dicom-web/servers/bar/stow -X POST -d @- << EOF
{
  "Resources" : [
    "ad5040ea-f640e840-9c9351be-4608e36e-7f5e8894"
  ]
}
EOF
```
- Open the second orthanc (bar) on [http://localhost:81](http://localhost:81).
- Check that the image is stored there.