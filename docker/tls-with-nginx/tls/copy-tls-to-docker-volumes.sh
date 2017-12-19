#!/usr/bin/env bash

# copy server certs and private keys to volumes used by nginx to implement the TLS layer in front of Orthanc
./_copy-tls-to-docker-volume.sh nginx-crt.pem nginx-key.pem tlswithnginx_nginx-tls