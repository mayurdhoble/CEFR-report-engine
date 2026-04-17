# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

# VITE_API_URL must be baked in at build time (Vite replaces it statically)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY . .
RUN npm run build

# ── Stage 2: serve ─────────────────────────────────────────────────────────────
FROM node:20-alpine

RUN npm install -g serve

COPY --from=builder /app/dist /app/dist

# Railway injects $PORT at runtime
CMD ["sh", "-c", "serve -s /app/dist -l ${PORT:-3000}"]
