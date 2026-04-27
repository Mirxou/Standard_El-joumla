FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --silent

COPY . .
RUN npm run build

ENV NODE_ENV=production
ENV API_URL=http://api:8000

EXPOSE 3000
CMD ["npm","start"]
