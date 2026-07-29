# Multi-stage: build web + API/worker (tudo num unico servico Render)
FROM node:20-slim AS web
WORKDIR /web
COPY apps/web/package.json ./
RUN npm install
COPY apps/web/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY backend/ ./
COPY --from=web /web/dist ./static

RUN chmod +x start-api.sh

EXPOSE 8000
CMD ["sh", "start-api.sh"]
