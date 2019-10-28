FROM osimis/orthanc
ENV DW_ENABLED true

# disable the auth defaults since we specify them in orthanc.json
ENV AC_BUNDLE_DEFAULTS=false

COPY orthanc.json /etc/orthanc/
COPY notify-external-web-service.lua /etc/share/orthanc/scripts/notify-external-web-service.lua
