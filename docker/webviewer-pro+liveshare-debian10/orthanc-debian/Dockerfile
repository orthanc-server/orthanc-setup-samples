FROM debian:10

RUN apt-get update && apt-get install -y orthanc apt-transport-https nano psmisc locales wget
RUN echo en_US.UTF-8 UTF-8 >> /etc/locale.gen
RUN echo en_US ISO-8859-1 >> /etc/locale.gen
RUN locale-gen
RUN mkdir -p /usr/share/orthanc/plugins/

# the orthanc debian package that has been installed is probably not the latest one -> replace all executables by the latest LSB binaries
# note: the orthanc debian package binaries are not LSB -> they are not compatible with LSB plugins -> we need to udpate all binaries to LSB !

RUN wget http://orthanc.osimis.io/lsb/orthanc/releases/1.5.7/Orthanc --output-document /usr/sbin/Orthanc --quiet
RUN wget http://orthanc.osimis.io/lsb/orthanc/releases/1.5.7/libModalityWorklists.so --output-document /usr/share/orthanc/plugins/libModalityWorklists.so --quiet
RUN wget http://orthanc.osimis.io/lsb/orthanc/releases/1.5.7/libServeFolders.so --output-document /usr/share/orthanc/plugins/libServeFolders.so --quiet
RUN wget http://orthanc.osimis.io/lsb/plugin-osimis-webviewer-pro/releases/1.3.0.0/libOsimisWebViewerPro.so --output-document /usr/share/orthanc/plugins/libOsimisWebViewerPro.so --quiet
RUN chmod +x /usr/sbin/*
RUN chmod +x /usr/share/orthanc/plugins/*
COPY orthanc.json /etc/orthanc/orthanc.json
ENTRYPOINT Orthanc /etc/orthanc/orthanc.json