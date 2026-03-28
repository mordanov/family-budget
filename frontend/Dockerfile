FROM node:20-alpine
WORKDIR /app
COPY package.json ./
COPY public ./public
RUN npm install --omit=dev
CMD ["npx", "http-server", "./public", "-p", "80"]

