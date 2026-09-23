FROM node:18-alpine

WORKDIR /app

# We assume the Next.js app is generated locally and we copy package.json
COPY dashboard/package*.json ./
RUN npm install

COPY dashboard/ ./

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
