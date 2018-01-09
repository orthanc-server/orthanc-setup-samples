#!/usr/bin/env bash

function writeFileToDockerVolume {
	echo "Writing $2 to $1"
	docker run --rm "--volume=$1:/mnt" --interactive \
		alpine dd "of=/mnt/$2"
}
# copy server certs and private keys to volumes used by nginx to implement the TLS layer in front of Orthanc

writeFileToDockerVolume tlswithnginx_nginx-tls nginx-crt.pem < nginx-crt.pem
writeFileToDockerVolume tlswithnginx_nginx-tls nginx-key.pem < nginx-key.pem

# copy root CA to orthanc-a so it accepts the self signed certificate of nginx when connecting to the orthanc-b peer
writeFileToDockerVolume tlswithnginx_orthanc-a-tls ca-crt.pem < ca-crt.pem
