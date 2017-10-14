FROM debian:8.9

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive apt-get -y install \
unzip wget curl \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# force install of "old" NodeJS 6.X 
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install nodejs

# download liveshare js code
RUN wget http://orthanc.osimis.io/public/wvp/live-share/latest.zip

RUN unzip latest.zip -d /liveshare

WORKDIR /liveshare
RUN npm install
ENTRYPOINT ["npm", "start"]
