FROM node:18
WORKDIR /app

COPY . .
RUN apt-get update && apt-get install -y bash
RUN npm install

EXPOSE 3000


CMD ["npm","start"]



