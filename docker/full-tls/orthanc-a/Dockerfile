FROM osimis/orthanc
ENV DW_ENABLED true

# disable http bundle since we're specifying http parameters in the orthanc.json configuration file
ENV HTTP_BUNDLE_DEFAULTS=false
# disable the auth defaults since we specify them in orthanc.json
ENV AC_BUNDLE_DEFAULTS=false

# note: DicomWeb 1.0 is not able to use Client Certificates -> use the mainline version instead (remove this line once next release of DicomWeb is available)
RUN wget https://lsb.orthanc-server.com/plugin-dicom-web/mainline/libOrthancDicomWeb.so --output-document /usr/share/orthanc/plugins-disabled/libOrthancDicomWeb.so --quiet

COPY orthanc.json /etc/orthanc/
