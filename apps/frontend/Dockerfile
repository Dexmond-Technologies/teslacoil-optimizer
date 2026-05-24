# ⚡ Tesla Coil Optimizer - Tactical HUD Dockerfile
FROM node:20-alpine

WORKDIR /workspace

# Install dependencies first for caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy sources
COPY . .

EXPOSE 5173

# Run the dev server with global host bindings
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
