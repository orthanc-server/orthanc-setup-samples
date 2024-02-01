FROM orthancteam/orthanc

# install gdcm and dcmtk that are used in a Lua scripts
RUN apt-get --assume-yes update
RUN	DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install dcmtk libgdcm-tools wget
RUN	DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install odbc-postgresql unixodbc-dev
RUN	DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install libsqliteodbc

#### note: this is not functional yet to validate mysql with odbc
# RUN	DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install apt-utils wget dpkg-dev lsb-release
# WORKDIR /tmp
# RUN wget https://repo.mysql.com/mysql-apt-config_0.8.20-1_all.deb
# RUN DEBIAN_FRONTEND=noninteractive dpkg -i *.deb
# RUN apt-get --assume-yes update
# RUN DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install mysql-community-client-plugins
# RUN DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install mysql-connector-odbc

COPY orthanc.json /etc/orthanc/orthanc.json
COPY odbc.ini /etc/
