# Multi-stage build for Vue 3 frontend

# Stage 1: Build Vue application
FROM node:20-alpine as builder

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
