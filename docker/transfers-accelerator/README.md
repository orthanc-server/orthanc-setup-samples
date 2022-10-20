# Purpose

This is a sample setup to demonstrate how to configure and run the [transfer accelerator plugin](https://book.orthanc-server.com/plugins/transfers.html).

# Description

This demo contains:

- 2 Orthanc instances.  Each instance is declared in the `OrthancPeers` 
  configuration of the other; this configuration is also used by the accelarator plugin.  
  They are both configured through environement variables only. 

To start, use `docker-compose up --build`.

To stop, use `docker-compose down`.

# demo

- Connect to the `orthanc-a` on [http://localhost:8042](http://localhost:8042) (demo/demo).
- Upload a study to this instance of Orthanc.
- Select the patient and then the study in the explorer
- Click on the yellow button entitled 'Transfers accelerator'
- Select `orthanc-b` in the list.

Right now, the study should be transferred to the second Orthanc:

- Open the second orthanc `orthanc-b` on [http://localhost:8043](http://localhost:8043) (demo/demo).
- Check that the study is stored there.