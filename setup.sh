#!/bin/bash
#-------------------------------------
# This script installs Orthanc on a fresh Ubuntu install (tested on Ubuntu 15.10 64bits).
#
# We'll run Orthanc inside docker so you can use the latest Orthanc version and don't have to wait
# until the official packages become available.
#
# We'll also configure supervisor to start Orthanc automatically as the server boots and restart Orthanc
# in the unlikely case it would crash.
#-------------------------------------

set -e                                                   #stops execution as soon as a command fails

currentDir=$(pwd)
currentUser=$(whoami)

#test if you have the right privileges to run this script
if [ ! -r "/etc/sudoers" ]; then
  echo "You must start this script as root or with sudo privileges"
  exit -1
fi


apt-get install -y docker.io supervisor


# configuration
#--------------

# select the image you'd like to install
dockerImage="osimis/orthanc-webviewer-plugin:latest"     # latest Orthanc with the Osimis webviewer plugin
# dockerImage="jodogne/orthanc-plugins"                  # latest Orthanc with all default plugins (Postgresql, Orthanc Web Viewer, worklist)
# dockerImage="jodogne/orthanc-plugins:1.0.0"            # Orthanc 1.0.0 with all default plugins (Postgresql, Orthanc Web Viewer, worklist)

# configure the ports used by Orthanc on the host machine (inside the container, Orthanc uses the ports defined in orthanc.json: 8042 and 4242 but you actually don't care about the internal ports so you should not modify them in orthanc.json)
hostHttpPort=80
hostDicomPort=4242

# configure the path where to store the configuration file and DB
hostOrthancConfigPath="$currentDir/orthanc.json"
hostOrthancStorage="$currentDir/OrthancStorage"
hostSupervisorLogs="$currentDir/OrthancLogs"


# Installation: Orthanc in docker
#--------------------------------

# create the storage directory
mkdir -p $hostOrthancStorage                    

# download the docker image
sudo docker pull $dockerImage                   

# retrieve the configuration file from the docker container (you will edit it later on)
docker run --rm --entrypoint=cat $dockerImage /etc/orthanc/orthanc.json > $hostOrthancConfigPath


# Installation: Supervisor
#-------------------------

echo "[program:orthanc]
command = sudo docker run -p $dicomHttpPort:4242 -p $hostHttpPort:8042 --rm -v $hostOrthancStorage:/var/lib/orthanc/db -v $hostOrthancConfigPath:/etc/orthanc/orthanc.json:ro $dockerImage ; Command to start app
user = $currentUser ; User to run as
stdout_logfile = $hostSupervisorLogs/orthanc_supervisor.log ; Where to write log messages
redirect_stderr = true ; Save stderr in the same log
environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8 ; Set UTF-8 as default encoding" | tee /etc/supervisor/conf.d/orthanc.conf > /dev/null

# create supervisor log files
mkdir -p $hostSupervisorLogs
touch $hostSupervisorLogs/orthanc_supervisor.log

# restart supervisor to take new settings into account
supervisorctl reload

# you should now be able to open http://localhost
# default credentials to login are orthanc/orthanc

# Maintenance
#------------

# if you wish to change the configuration, edit the orthanc.json file and restart the supervisor with:
# sudo supervisorctl reload

# if you wish to update the docker image to another version:
# sudo docker pull $dockerImage
# sudo supervisorctl restart orthanc