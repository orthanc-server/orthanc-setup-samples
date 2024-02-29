#!/bin/bash
# lots of useful info grabbed from https://engineering.circle.com/https-authorized-certs-with-node-js-315e548354a2
#
# warning: this scripts are not intended to be used in a production environment.  Always ask a security expert !

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout pacs-with-tls-key.pem -out pacs-with-tls-crt.pem -subj "/C=BE/CN=pacs-with-tls"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout orthanc-with-tls-key.pem -out orthanc-with-tls-crt.pem -subj "/C=BE/CN=orthanc-with-tls"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout modality-with-tls-key.pem -out modality-with-tls-crt.pem -subj "/C=BE/CN=modality-with-tls"

cat pacs-with-tls-crt.pem orthanc-with-tls-crt.pem modality-with-tls-crt.pem  > trusted-all-crt.pem
cat pacs-with-tls-crt.pem orthanc-with-tls-crt.pem                            > trusted-pacs-orthanc-crt.pem
