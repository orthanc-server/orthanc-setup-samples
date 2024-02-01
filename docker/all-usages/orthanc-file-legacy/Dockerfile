FROM orthancteam/orthanc

ENV WEVB_ENABLED=true

# disable the auth defaults since we specify them in orthanc.json
ENV AC_BUNDLE_DEFAULTS=false

COPY orthanc.json /etc/orthanc/
