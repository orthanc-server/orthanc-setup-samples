# as of Nov 2021, msodbcsql is not available on bullseye yet -> you need to use the buster image
FROM osimis/orthanc:21.10.0-buster

RUN apt-get update
RUN apt-get --assume-yes install curl gnupg2

RUN mkdir /downloads

RUN curl https://packages.microsoft.com/keys/microsoft.asc > /downloads/microsoft.asc
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-key add /downloads/microsoft.asc
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev mssql-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /scripts

# debug tools to show MSSQL cert
# COPY orthanc/get_tds_cert.py /scripts/


# from https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/connection-string-keywords-and-data-source-names-dsns?view=sql-server-ver15#using-tlsssl
COPY tls/mssql.pem /etc/ssl/certs/mssql.pem

# from https://docs.microsoft.com/en-us/sql/linux/sql-server-linux-encrypted-connections?view=sql-server-ver15#client-initiated-encryption
COPY tls/mssql.pem /usr/share/ca-certificates/mssql.crt
RUN dpkg-reconfigure ca-certificates