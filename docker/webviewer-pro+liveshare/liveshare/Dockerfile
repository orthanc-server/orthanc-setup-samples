FROM node:6.9.1

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive apt-get -y install \
unzip \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# download liveshare js code
RUN wget http://orthanc.osimis.io/public/wvp/live-share/1.3.0.0.zip

RUN unzip 1.3.0.0.zip -d /liveshare

WORKDIR /liveshare
RUN npm install
ENTRYPOINT ["npm", "start"]

