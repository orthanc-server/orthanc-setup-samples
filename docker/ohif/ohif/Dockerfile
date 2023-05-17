######################################################

FROM node:16.15.0-slim as builder

RUN apt-get update && apt-get install -y git

WORKDIR /sources
# v3-stable branch on 2023.05.11
RUN git clone https://github.com/OHIF/Viewers.git && cd /sources/Viewers && git checkout 84cb709b44074c7553fabd28bbcd2da4c1bd60d6

WORKDIR /sources/Viewers

RUN yarn install --frozen-lockfile --verbose

ENV QUICK_BUILD true
# ENV GENERATE_SOURCEMAP=false
# ENV REACT_APP_CONFIG=config/default.js

RUN yarn install 
RUN QUICK_BUILD=true PUBLIC_URL=/ohif/ yarn run build

######################################################

FROM nginx:1.23

RUN mkdir /etc/nginx/enabled-sites
RUN mkdir /scripts

COPY ohif-static.conf /etc/nginx/enabled-sites/
ADD ohif-nginx-http.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /sources/Viewers/platform/viewer/dist /usr/share/nginx/html/
COPY default-app-config.js /usr/share/nginx/html/app-config.js