FROM mcr.microsoft.com/mssql/server

USER root
RUN mkdir /scripts

COPY create-database.sh /scripts/
COPY entrypoint.sh /scripts/

USER mssql
ENTRYPOINT /bin/bash ./scripts/entrypoint.sh