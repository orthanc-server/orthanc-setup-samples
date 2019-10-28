FROM osimis/orthanc

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive apt-get -y install \
libgdcm-tools \
dcmtk \
apt-transport-https \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# disable the auth defaults since we specify them in orthanc.json
ENV AC_BUNDLE_DEFAULTS=false

RUN mkdir -p /etc/share/orthanc/scripts
COPY orthanc.json /etc/orthanc/
COPY transcodeAndForward.lua /etc/share/orthanc/scripts/
