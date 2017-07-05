#!/bin/bash
# lots of useful info grabbed from https://engineering.circle.com/https-authorized-certs-with-node-js-315e548354a2
#
# warning: this scripts are not intended to be used in a production environment.  Always ask a security expert !

# generate a new certificate authority
#-------------------------------------
openssl req -new -x509 -days 9999 -config ca.cnf -keyout ca-key.pem -out ca-crt.pem

# server
#-------

# generate a private key for the orthanc-servers (that will be used by nginx)
openssl genrsa -out orthanc-a-server-key.pem 4096
openssl genrsa -out orthanc-b-server-key.pem 4096
openssl genrsa -out external-web-service-key.pem 4096

# generate a CSR (Certificate Signing Request) for the server certificate with the server private key
openssl req -new -config orthanc-a-server.cnf -key orthanc-a-server-key.pem -out orthanc-a-server-csr.pem
openssl req -new -config orthanc-b-server.cnf -key orthanc-b-server-key.pem -out orthanc-b-server-csr.pem
openssl req -new -config external-web-service.cnf -key external-web-service-key.pem -out external-web-service-csr.pem

# now let's sign the requests with our CA
openssl x509 -req -extfile orthanc-a-server.cnf -days 999 -passin "pass:password" -in orthanc-a-server-csr.pem -CA ca-crt.pem -CAkey ca-key.pem -CAcreateserial -out orthanc-a-server-crt.pem
openssl x509 -req -extfile orthanc-b-server.cnf -days 999 -passin "pass:password" -in orthanc-b-server-csr.pem -CA ca-crt.pem -CAkey ca-key.pem -CAcreateserial -out orthanc-b-server-crt.pem
openssl x509 -req -extfile external-web-service.cnf -days 999 -passin "pass:password" -in external-web-service-csr.pem -CA ca-crt.pem -CAkey ca-key.pem -CAcreateserial -out external-web-service-crt.pem

# clients
#--------

# let's generate 2 private key for 2 clients certificates
openssl genrsa -out orthanc-a-client-key.pem 4096
openssl genrsa -out orthanc-b-client-key.pem 4096

# Now let’s create a pair of certificate signing requests.
openssl req -new -config orthanc-a-client.cnf -key orthanc-a-client-key.pem -out orthanc-a-client-csr.pem
openssl req -new -config orthanc-b-client.cnf -key orthanc-b-client-key.pem -out orthanc-b-client-csr.pem

# now let's sign the requests with our CA
openssl x509 -req -extfile orthanc-a-client.cnf -days 999 -passin "pass:password" -in orthanc-a-client-csr.pem -CA ca-crt.pem -CAkey ca-key.pem -CAcreateserial -out orthanc-a-client-crt.pem
openssl x509 -req -extfile orthanc-b-client.cnf -days 999 -passin "pass:password" -in orthanc-b-client-csr.pem -CA ca-crt.pem -CAkey ca-key.pem -CAcreateserial -out orthanc-b-client-crt.pem


# verification
#-------------
openssl verify -CAfile ca-crt.pem orthanc-a-client-crt.pem
openssl verify -CAfile ca-crt.pem orthanc-a-client-crt.pem
openssl verify -CAfile ca-crt.pem orthanc-a-server-crt.pem
openssl verify -CAfile ca-crt.pem orthanc-b-server-crt.pem
openssl verify -CAfile ca-crt.pem external-web-service-crt.pem
