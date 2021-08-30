# note: we need a recent version with DCMTK 3.6.5+ (e.g: 21.8.2+)
FROM osimis/orthanc

RUN mkdir /tls

# note: build context is one folder up this one
COPY tls/orthanc-a-server-key.pem /tls
COPY tls/orthanc-a-server-crt.pem /tls
COPY tls/trusted-crt.pem /tls

COPY orthanc-a-server/orthanc.json /etc/orthanc/

ENV VERBOSE_ENABLED true