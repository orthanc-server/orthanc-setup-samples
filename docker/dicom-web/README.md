To start, use `docker-compose up --build -d`.
To stop, use `docker-compose down`.

# demo

- Connect to the orthanc A on [http://localhost:80](http://localhost:80) login/pwd = demo/demo.
- Upload an image to this instance of Orthanc.
- browse to the study and select "Send to DicomWeb Server"
- send the study to b
- Open the second orthanc B on [http://localhost:81](http://localhost:81) login/pwd = demo/demo.
- Check that the image is stored there.