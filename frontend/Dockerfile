# syntax=docker/dockerfile:1.7
# ============================================================
# Hotel Booking — Frontend
# Multi-stage build: install + build → nginx static serve.
# In production we use Vercel (which runs the npm scripts itself),
# this Dockerfile is for optional local production-like testing.
# ============================================================

# --- Stage 1: build the static bundle
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: serve the dist/ folder with nginx
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1
