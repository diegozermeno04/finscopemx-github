# frontend/Dockerfile
# Multi-stage build for the React/Vite frontend.
# Stage 1 installs dependencies and compiles the production bundle.
# Stage 2 serves the static bundle via Nginx.

# ── Stage 1: Node builder ──────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first to leverage Docker layer cache.
# npm install only re-runs when package.json or package-lock.json change.
COPY package.json package-lock.json ./
RUN npm ci --silent

# Inject Vite build-time environment variables.
# These are passed from docker-compose.yml build args.
ARG VITE_API_BASE_URL
ARG VITE_APP_ENV
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_APP_ENV=$VITE_APP_ENV

COPY . .
RUN npm run build

# ── Stage 2: Nginx static server ──────────────────────────────
FROM nginx:alpine AS runtime

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy compiled bundle from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a minimal Nginx config for the SPA.
# This config handles React Router client-side routing
# by falling back to index.html for all non-asset routes.
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
