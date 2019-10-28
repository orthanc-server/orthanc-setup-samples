FROM osimis/orthanc

# disable http bundle since we're specifying http parameters in the orthanc.json configuration file
ENV HTTP_BUNDLE_DEFAULTS=false
# disable the auth defaults since we specify them in orthanc.json
ENV AC_BUNDLE_DEFAULTS=false

COPY orthanc.json /etc/orthanc/
