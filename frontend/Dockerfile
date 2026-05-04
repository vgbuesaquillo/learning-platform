# ── Etapa base ──────────────────────────────────────────────
FROM node:20-alpine AS base
WORKDIR /app

# ── Dependencias ─────────────────────────────────────────────
FROM base AS deps
COPY package.json package-lock.json* ./
RUN npm install

# ── Development (hot-reload) ──────────────────────────────────
FROM base AS development
COPY --from=deps /app/node_modules ./node_modules
# El código fuente se monta como volumen en docker-compose
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ── Build ─────────────────────────────────────────────────────
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ── Production ────────────────────────────────────────────────
FROM base AS production
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
