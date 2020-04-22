FROM osimis/orthanc

# install gdcm and dcmtk that are used in a Lua scripts
RUN apt-get --assume-yes update
RUN	DEBIAN_FRONTEND=noninteractive apt-get --assume-yes install dcmtk libgdcm-tools 

COPY orthanc.json /etc/orthanc/orthanc.json
