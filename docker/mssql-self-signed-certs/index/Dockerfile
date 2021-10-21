FROM mcr.microsoft.com/mssql/server:2019-latest

USER root

RUN mkdir /scripts

COPY index/create-database.sh /scripts/
COPY index/entrypoint.sh /scripts/

# USER mssql  run as root to ensure easy access to cert+key files
ENTRYPOINT /bin/bash ./scripts/entrypoint.sh

