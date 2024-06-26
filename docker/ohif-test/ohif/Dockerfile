######################################################

FROM node:18.16.1-slim AS builder

RUN apt-get update && apt-get install -y git build-essential python3

WORKDIR /sources
RUN git clone https://github.com/OHIF/Viewers.git && cd /sources/Viewers && git checkout 6c9a4d9758a72f0aca7c941dc676df0ec12b973f
RUN cp -r /sources/ /usr/src/app/
RUN ls -al /usr/src/app/

WORKDIR /usr/src/app

# Run the install before copying the rest of the files
RUN yarn config set workspaces-experimental true
RUN yarn install --frozen-lockfile --verbose

ENV PATH /usr/src/app/node_modules/.bin:$PATH
ENV QUICK_BUILD true
# ENV GENERATE_SOURCEMAP=false
# ENV REACT_APP_CONFIG=config/default.js

RUN yarn run build

# Stage 3: Bundle the built application into a Docker container
# which runs Nginx using Alpine Linux
FROM nginxinc/nginx-unprivileged:1.25-alpine as final
#RUN apk add --no-cache bash
ENV PORT=80
RUN rm /etc/nginx/conf.d/default.conf
USER nginx
COPY --chown=nginx:nginx --from=builder /sources/.docker/Viewer-v3.x /usr/src
RUN chmod 777 /usr/src/entrypoint.sh
COPY --from=builder /usr/src/app/platform/app/dist /usr/share/nginx/html
# In entrypoint.sh, app-config.js might be overwritten, so chmod it to be writeable.
# The nginx user cannot chmod it, so change to root.
USER root
RUN chmod 666 /usr/share/nginx/html/app-config.js
USER nginx
ENTRYPOINT ["/usr/src/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
