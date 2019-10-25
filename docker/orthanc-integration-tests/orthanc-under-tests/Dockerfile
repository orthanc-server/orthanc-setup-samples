FROM osimis/orthanc:19.10.2

# install gdcm and dcmtk that are used in a Lua scripts
RUN apt-get --assume-yes update
RUN	DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install dcmtk libgdcm-tools 

# disable the auth defaults since we specify them in orthanc.json
ENV AC_BUNDLE_DEFAULTS=false

COPY orthanc.json /etc/orthanc/orthanc.json
