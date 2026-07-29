# Story2 - Story R Us MVP

Plataforma para gerar ebooks infantis personalizados: o usuario envia a foto da crianca, escolhe uma historia pronta e recebe um PDF ilustrado.

## Subir localmente

```bash
cd Story2
cp .env.example backend/.env
docker compose up --build
```

- Web: http://localhost:5174
- API docs: http://localhost:8001/docs
- MinIO console: http://localhost:9101 (story2 / story2123456)

Ports no compose (para nao conflitar com o projeto antigo):
Postgres 5433, Redis 6380, MinIO 9100/9101, API 8001, Web 5174.

Sem GEMINI_API_KEY, o worker gera placeholders coloridos (modo offline) para testar o fluxo completo.

## Fluxo

1. Criar conta / entrar
2. Informar nome, idade, genero e foto da crianca
3. Escolher uma das 3 historias e a faixa etaria do texto (automatica pela idade ou manual: 2-5, 5-9, 6-9, 9-12)
4. Aguardar geracao (personagem -> cenas -> PDF)
5. Baixar o ebook

## Stack

React (Vite) / FastAPI / Postgres / Redis / MinIO / Gemini (imagens) / ReportLab (PDF)