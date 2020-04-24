FROM osimis/orthanc:current

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive apt-get -y install \
libgdcm-tools \
dcmtk \
apt-transport-https \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

RUN pip3 install requests

ENV VERBOSE_STARTUP=true
ENV VERBOSE_ENABLED=true
COPY orthanc.json /etc/orthanc/
COPY *.py /python/
