FROM node:6.9.1

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive apt-get -y install \
unzip \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# download liveshare js code
RUN wget http://orthanc.osimis.io/public/wvp/live-share/latest.zip

RUN unzip latest.zip -d /liveshare

WORKDIR /liveshare
RUN npm install
ENTRYPOINT ["npm", "start"]

