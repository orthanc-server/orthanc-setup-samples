To start, use `docker-compose up -d`.
To stop, use `docker-compose down`.

# demo

- Connect to the orthanc A on [http://localhost:8045/ui/app/](http://localhost:8045/ui/app/) login/pwd = demo/demo.
- Upload an image to this instance of Orthanc.
- browse to the study and select "Send to DicomWeb Server"
- send the study to b
- Open the second orthanc B on [http://localhost:8046/ui/app/](http://localhost:8046/ui/app/) login/pwd = demo/demo.
- Check that the image is stored there.