FROM osimis/orthanc

RUN apt-get update
RUN apt-get --assume-yes install curl gnupg2

RUN mkdir /downloads

RUN curl https://packages.microsoft.com/keys/microsoft.asc > /downloads/microsoft.asc
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-key add /downloads/microsoft.asc
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*