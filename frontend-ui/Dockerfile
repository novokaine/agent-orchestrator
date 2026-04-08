# Multi-stage build
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including dev for build)
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install nginx and dumb-init
RUN apk add --no-cache nginx dumb-init

# Copy production dependencies only
COPY package*.json ./
RUN npm ci --only=production

# Copy built React app
COPY --from=builder /app/dist /app/dist

# Copy WebSocket server (now .cjs) and configs
COPY websocket-server.js /app/ 
COPY entrypoint.sh /app/entrypoint.sh
COPY nginx.conf /etc/nginx/nginx.conf

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create necessary directories
RUN mkdir -p /run/nginx /var/log/nginx

EXPOSE 80 3001

ENTRYPOINT ["dumb-init", "/app/entrypoint.sh"]