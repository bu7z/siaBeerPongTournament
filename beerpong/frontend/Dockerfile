FROM node:20-alpine

WORKDIR /app

# 1. nur package*.json kopieren → so nutzt Docker Cache
COPY package*.json ./

# 2. deps installieren
RUN npm install

# 3. Rest vom Code
COPY . .

# 4. Vite im Dev-Modus starten
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
