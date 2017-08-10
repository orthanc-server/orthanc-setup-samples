FROM node:8-alpine

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Bundle app source
COPY web-service.js /usr/src/app/web-service.js

CMD [ "node", "web-service.js" ]