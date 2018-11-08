To start, use `docker-compose up --build -d`.
To stop, use `docker-compose down`.

# demo

- Connect to the orthanc 'foo' on [http://localhost:80](http://localhost:80).
- Upload a study to this instance of Orthanc.
- Select the patient and then the study in the explorer
- Click on the yellow button entitled 'Transfers accelerator'
- Select 'bar' in the list.

Right now, the study should be transferred to the second Orthanc (bar) :

- Open the second orthanc (bar) on [http://localhost:81](http://localhost:81).
- Check that the study is stored there.