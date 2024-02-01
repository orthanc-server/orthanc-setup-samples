FROM orthancteam/orthanc

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive apt-get -y install \
libgdcm-tools \
dcmtk \
apt-transport-https \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/share/orthanc/scripts

COPY orthanc.json /etc/orthanc/
COPY transcodeAndForward.lua /etc/share/orthanc/scripts/
