#!/bin/bash
#-------------------------------------
# This script installs Orthanc on a fresh Ubuntu install (tested on Ubuntu 15.10 64bits).
#
# We'll run Orthanc inside docker so you can use the latest Orthanc version and don't have to wait
# until the official packages become available.
#
# We'll also configure supervisor to start Orthanc automatically as the server boots and restart Orthanc
# in the unlikely case it would crash.
#
# Disclaimer: this script is provided as is without any guarantee.  It should not be used as such in
# a production environment.  Before running it, make sure you understand each step.
#-------------------------------------

set -e                                                   #stops execution as soon as a command fails
set -x                                                   #displays each step of the script

currentDir=$(pwd)
currentUser=$(whoami)

#test if you have the right privileges to run this script
if [ ! -r "/etc/sudoers" ]; then
  echo "You must start this script as root or with sudo privileges"
  exit -1
fi


apt-get update
apt-get install -y docker.io supervisor


# configuration
#--------------

# select the image you'd like to install
dockerImage="osimis/orthanc-webviewer-plugin"     # latest Orthanc with the Osimis webviewer plugin and Orthanc default plubins (Postgresql, DicomWeb, worklist)
# dockerImage="jodogne/orthanc-plugins:1.0.0"            # Orthanc 1.0.0 with all default plugins (Postgresql, Orthanc Web Viewer, worklist)

# configure the ports used by Orthanc on the host machine (inside the container, Orthanc uses the ports defined in orthanc.json: 8042 and 4242 but you actually don't care about the internal ports so you should not modify them in orthanc.json)
hostHttpPort=80
hostDicomPort=4242

#enable postgresql (set it to 1 to enable it) 
enablePostgresql=1


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


# Installation: postgresql
#-------------------------
if [ "1" -eq "$enablePostgresql" ]; then
  apt install -y postgresql postgresql-contrib libpq-dev expect

  #create a user and the db (local database for now). 
  # for this, we need a dedicated script executed by expect to handle the "interactive" prompt
  sudo apt install -y expect
  echo "spawn sudo su - postgres
  expect \"$ \"
  send \"psql -c \\\"CREATE USER orthanc WITH PASSWORD 'pgpassword'\\\"\r\"
  send \"createdb --owner orthanc orthanc\r\"
  send \"logout\r\"
  expect eof" | tee setupPostgresql.sh > /dev/null
  chmod 755 setupPostgresql.sh
  /usr/bin/expect ./setupPostgresql.sh

  #retrieve the ip address of the host from inside the container
  hostIp=$(docker run --rm --entrypoint=netstat $dockerImage -nr | grep '^0\.0\.0\.0' | awk '{print $2}')
  
  #configure postgresql to listen from any IP (note: you should probably restrict to your docker container only)
  echo "listen_addresses = '*'" | sudo tee --append /etc/postgresql/9.4/main/postgresql.conf > /dev/null
  echo "host     all             all             0.0.0.0/0               md5" | sudo tee --append /etc/postgresql/9.4/main/pg_hba.conf > /dev/null

  service postgresql restart

  #inject the postgres configuration in the orthanc config file
  sed -i '$ s/.$//' orthanc.json    #remove last character of config file ('}')
  echo ",
    \"PostgreSQL\" : {
    \"EnableIndex\" : true,
    \"EnableStorage\" : true,
    \"Host\" : \"$hostIp\",
    \"Port\" : 5432,
    \"Database\" : \"orthanc\",
    \"Username\" : \"orthanc\",
    \"Password\" : \"pgpassword\"
    }
  }" | tee --append orthanc.json > /dev/null
fi

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

#restart docker (it happens that Orthanc can't connect to postgresql before this restart ...)
service docker restart

# you should now be able to open http://localhost
# default credentials to login are orthanc/orthanc

# Maintenance
#------------

# if you wish to change the configuration, edit the orthanc.json file and restart the supervisor with:
# sudo supervisorctl reload

# if you wish to update the docker image to another version:
# sudo docker pull $dockerImage
# sudo supervisorctl restart orthanc

# Troubleshooting
#----------------

# check OrthancLogs/orthanc_supervisor.log to get the Orthanc output