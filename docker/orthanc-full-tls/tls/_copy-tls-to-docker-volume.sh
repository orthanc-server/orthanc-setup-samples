#!/usr/bin/env bash

function usage {
	cat <<-EOF >&2
	Usage: $(basename "$0") [-h] CERT PRIVKEY VOL

	CERT is a path to a certificate file in a format supported by
	nginx, usually PEM.

	PRIVKEY is a path to the private key corresponding to the public
	key certified by CERT in a format supported by nginx, usually PEM.

	VOL is the name of the Docker named volume which holds TLS data
	for the nginx reverse proxy of Lify, usually lify_tls.


	This procedure is independent, you may install it as-is and
	execute it anywhere.

	Example: when generating self signed certificates, use, i.e:
	------------------------------------------------------------
	local$ openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout /tmp/private.key -out /tmp/certificate.crt
	local$ ./setupTls.sh /tmp/certificate.crt /tmp/private.key vete_tls
	EOF
}

while getopts h opt; do
	case $opt in
	h) usage && exit;;
	?) usage && exit 1;;
	esac
done
shift $((OPTIND-1))
if (($# != 3)); then
	usage
	exit 1
fi
cert=$1
privkey=$2
vol=$3

function writeFile {
	docker run --rm "--volume=$vol:/mnt" --interactive \
		alpine dd "of=/mnt/$1"
}

echo "Writing certificate \"$cert\" in volume \"$vol\"" >&2
if ! writeFile cert.pem <$cert
then
	echo "Could not write certificate" >&2
	exit 2
fi

echo "Writing private key \"$privkey\" in volume \"$vol\"" >&2
if ! writeFile privkey.pem <$privkey
then
	echo "Could not write private key" >&2
	exit 3
fi