# Purpose

This is a sample setup to demonstrate how to configure Orthanc with HTTPS.

In this demo, we are using self-signed certificate but, for a real life system,
you should of course use certificate signed by a standard CA authority.

This demo also enables the OHIF viewer to validate that it works correctly in a HTTP environment
(this is required for using e.g. `SharedArrayBuffer`)

# Description

This demo contains:

- a script to generate self-signed certificate
- an Orthanc container.

# Starting the setup

- First, you'll need to generate keys and certificates for all modules.  Go in the `tls` folder and type `generate-tls.sh`
- To start the setup, type: `docker-compose up`

# demo

- Orthanc UI is accessible at [https://localhost/ui/app/](https://localhost/ui/app/).  Since you are using self-signed
  certificate, your browser should complain that the connection is not secure.
- upload a study to Orthanc A
- once the study has been uploaded, open it in the OHIF viewer.
- note the IP address of your machine e.g: `192.168.0.10` and make sure your firewall does not block port 443
- from a remote computer, open `https://192.168.0.10/ui/app/`
