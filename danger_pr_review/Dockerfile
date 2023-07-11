FROM node:18.15.0-alpine3.16

COPY . /
WORKDIR /dangerjs

# Install dependencies
RUN npm install

ENTRYPOINT ["sh", "/entrypoint.sh"]
