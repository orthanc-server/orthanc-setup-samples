#!/bin/bash
# lots of useful info grabbed from https://engineering.circle.com/https-authorized-certs-with-node-js-315e548354a2
#
# warning: this scripts are not intended to be used in a production environment.  Always ask a security expert !

# generate a new certificate authority
#-------------------------------------
openssl req -new -x509 -days 9999 -config ca.cnf -keyout ca-key.pem -out ca-crt.pem

# server
#-------

# generate a private key for the Orthanc server
openssl genrsa -out orthanc-private-key.pem 4096

# generate a CSR (Certificate Signing Request) for the server certificate with the server private key
openssl req -new -config orthanc.cnf -key orthanc-private-key.pem -out orthanc-csr.pem

# now let's sign the requests with our CA
openssl x509 -req -extfile orthanc.cnf -days 999 -passin "pass:password" -in orthanc-csr.pem -CA ca-crt.pem -CAkey ca-key.pem -CAcreateserial -out orthanc-crt.pem

# verification
#-------------
openssl verify -CAfile ca-crt.pem orthanc-crt.pem

# concatenate the certificate and the private key
cat orthanc-private-key.pem orthanc-crt.pem > orthanc-https.pem