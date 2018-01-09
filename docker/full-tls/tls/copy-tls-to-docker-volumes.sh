#!/usr/bin/env bash

function writeFileToDockerVolume {
	docker run --rm "--volume=$1:/mnt" --interactive \
		alpine dd "of=/mnt/$2"
}

# copy server certs and private keys to volumes used by nginx to implement the TLS layer in front of Orthanc
./_copy-tls-to-docker-volume.sh orthanc-a-server-crt.pem orthanc-a-server-key.pem fulltls_orthanc-a-server-tls
./_copy-tls-to-docker-volume.sh orthanc-b-server-crt.pem orthanc-b-server-key.pem fulltls_orthanc-b-server-tls

# nginx-b will perform some client certificate checks -> it needs the CA
echo "Writing CA cert to nginx-b"
writeFileToDockerVolume fulltls_orthanc-b-server-tls ca-crt.pem < ca-crt.pem

./_copy-tls-to-docker-volume.sh orthanc-a-client-crt.pem orthanc-a-client-key.pem fulltls_orthanc-a-tls
echo "Writing CA cert to orthanc-a-tls"
writeFileToDockerVolume fulltls_orthanc-a-tls ca-crt.pem < ca-crt.pem

./_copy-tls-to-docker-volume.sh orthanc-b-client-crt.pem orthanc-b-client-key.pem fulltls_orthanc-b-forward-proxy-tls
echo "Writing CA cert to orthanc-b-forward-proxy"
writeFileToDockerVolume fulltls_orthanc-b-forward-proxy-tls ca-crt.pem < ca-crt.pem

./_copy-tls-to-docker-volume.sh external-web-service-crt.pem external-web-service-key.pem fulltls_external-web-service-tls
echo "Writing CA cert to orthanc-b-forward-proxy"
writeFileToDockerVolume fulltls_external-web-service-tls ca-crt.pem < ca-crt.pem

