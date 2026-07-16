# Node gateway — the only public-facing service.
FROM node:20-slim

WORKDIR /app

# Install deps first for layer caching.
COPY package*.json ./
RUN npm install --omit=dev

COPY . .

EXPOSE 8787

CMD ["node", "server.js"]
