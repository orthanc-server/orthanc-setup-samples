FROM orthancteam/orthanc

COPY download-config.lua /scripts/

# overwrite the default entrypoint.  We only want to use the configuration files in /etc/orthanc -> no use of Docker environment variables !
ENTRYPOINT ["/usr/local/bin/Orthanc", "--verbose", "/etc/orthanc/"]