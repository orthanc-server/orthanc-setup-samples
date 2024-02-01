# note: we need a recent version with DCMTK 3.6.5+ (e.g: 21.8.2+)
FROM orthancteam/orthanc

RUN mkdir /tls

# note: build context is one folder up this one
COPY tls/orthanc-b-server-key.pem /tls
COPY tls/orthanc-b-server-crt.pem /tls
COPY tls/trusted-crt.pem /tls

COPY orthanc-b-server/orthanc.json /etc/orthanc/

ENV VERBOSE_ENABLED true