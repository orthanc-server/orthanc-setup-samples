#!/bin/bash
# lots of useful info grabbed from https://engineering.circle.com/https-authorized-certs-with-node-js-315e548354a2
#
# warning: this scripts are not intended to be used in a production environment.  Always ask a security expert !

# generate a self signed certificate for the server and one for the client

openssl req -x509 -nodes -days 9999 -config server.cnf -keyout server-key.pem -out server-crt.pem
openssl req -x509 -nodes -days 9999 -config client.cnf -keyout client-key.pem -out client-crt.pem

cat server-crt.pem server-key.pem > server-crt+key.pem