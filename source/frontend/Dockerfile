# source/frontend/Dockerfile
#
# Image du frontend Next.js. Build depuis la RACINE du repo (contexte),
# pour rester coherent avec source/backend/Dockerfile.
#
#   docker build -f source/frontend/Dockerfile -t globatrend-frontend .
#   docker compose build frontend

FROM node:22-slim AS base
RUN corepack enable
WORKDIR /app

FROM base AS deps
COPY source/frontend/package.json source/frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY source/frontend/ ./
ENV NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
RUN pnpm build

FROM base AS runner
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
