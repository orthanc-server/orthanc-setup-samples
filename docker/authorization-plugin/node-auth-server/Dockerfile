FROM node:8-alpine

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Bundle app source
COPY auth-service.js /usr/src/app/auth-service.js

CMD [ "node", "auth-service.js" ]