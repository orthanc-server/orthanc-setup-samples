#!/bin/bash
# lots of useful info grabbed from https://engineering.circle.com/https-authorized-certs-with-node-js-315e548354a2
#
# warning: this scripts are not intended to be used in a production environment.  Always ask a security expert !


openssl req -x509 -nodes -newkey rsa:2048 -subj '/CN=index-mssql' -keyout mssql.key -out mssql.pem -days 365

