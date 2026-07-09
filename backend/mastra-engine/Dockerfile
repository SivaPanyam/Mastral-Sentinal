FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

RUN npx tsc

EXPOSE 3000

CMD ["node", "dist/server.js"]
