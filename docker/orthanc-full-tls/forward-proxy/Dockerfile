FROM node:8-alpine

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Bundle app source
COPY forward-proxy.js /usr/src/app/forward-proxy.js

CMD [ "node", "forward-proxy.js" ]