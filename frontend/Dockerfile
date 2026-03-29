FROM node:25.0-alpine
WORKDIR /app
COPY package.json ./
COPY public ./public
RUN npm install --omit=dev
CMD ["npx", "http-server", "./public", "-p", "80"]

