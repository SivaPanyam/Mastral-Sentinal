FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

COPY . .

RUN npm install -g tsx
EXPOSE 3000

CMD ["tsx", "src/server.ts"]
