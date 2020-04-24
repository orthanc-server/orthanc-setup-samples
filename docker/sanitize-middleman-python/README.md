# Purpose

This is a sample setup to demonstrate how an Orthanc instance can be used to serve as a middleman to sanitize images between a modality and a PACS.
Compared to the [transcode middleman](../transcode-middleman) sample that is using Lua, this sample uses Python.
This middleman will also implement retries and recovery after a switch on/off which is not the case with the lua sample.

# Description

This demo contains:

- an Orthanc-modality container that simulates a modality. 
- an Orthanc-middleman container that serves as a 'proxy' between the modalities and the PACS to transcode the images to JP2K and sanitize
  the InstitutionName tag before pushing the images to the PACS.
- an Orthanc-pacs container that simulates a PACS.


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
- Check the `InstitutionName` tag, it shall now contain "MY NEW INSTITUTION"
- you can start/stop the pacs container and see that the middleman will retry sending the data.
- you can also stop the middleman while it still has data inside and you'll see that, when restarting, it will retry to send the data to the pacs