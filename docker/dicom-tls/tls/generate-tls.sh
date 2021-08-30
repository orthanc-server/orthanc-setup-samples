#!/bin/bash
# lots of useful info grabbed from https://engineering.circle.com/https-authorized-certs-with-node-js-315e548354a2
#
# warning: this scripts are not intended to be used in a production environment.  Always ask a security expert !

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout orthanc-a-server-key.pem -out orthanc-a-server-crt.pem -subj "/C=BE/CN=orthanc-a-server"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout orthanc-b-server-key.pem -out orthanc-b-server-crt.pem -subj "/C=BE/CN=orthanc-b-server"

cat orthanc-a-server-crt.pem orthanc-b-server-crt.pem > trusted-crt.pem
