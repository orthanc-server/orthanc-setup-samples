FROM osimis/orthanc

# disable the auth defaults since we specify them in orthanc.json
ENV AC_BUNDLE_DEFAULTS=false

COPY orthanc.json /etc/orthanc/
COPY cfind-filter.lua /etc/orthanc/
