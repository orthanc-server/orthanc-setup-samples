# Purpose

This is a sample setup to demonstrate how an Orthanc instance can be used to serve as a middleman to transcode images between a modality and a PACS.

# Description

This demo contains:

- an Orthanc-pacs container that simulates a PACS.
- an Orthanc-middleman container that serves as a 'proxy' between the modalities and the PACS to transcode the images to JP2K before pushing the images to the PACS.
- an Orthanc-modality container that simulates a modality. 


# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- login/pwd = demo/demo
- Connect to the orthanc simulating the modality on [http://localhost:8044](http://localhost:8044).
- Upload an image to this instance of Orthanc.
- In the Orthanc explorer, open the study, select 'send to modality', select the 'middleman' and send
- the instance is forwarded to the middleman that will transcode the image, forward it to the PACS and delete it from its storage (the middleman is just a temporary buffer)
- Open the orthanc simulating the PACS on [http://localhost:8042](http://localhost:8042).
- The image that is stored there is now in JP2K.