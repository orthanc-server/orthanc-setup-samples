FROM debian:8.9

RUN apt-get update && apt-get install -y apt-transport-https nano psmisc locales
RUN echo en_US.UTF-8 UTF-8 >> /etc/locale.gen
RUN echo en_US ISO-8859-1 >> /etc/locale.gen
RUN locale-gen
RUN echo "deb http://orthanc.osimis.io/debian/8.3/1.3.0-1.0.0.1 jessie partner" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y --force-yes osimis-orthanc
COPY orthanc.json /etc/orthanc/orthanc.json
ENTRYPOINT Orthanc /etc/orthanc/orthanc.json