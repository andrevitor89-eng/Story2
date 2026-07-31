# Story2 - Story R Us MVP

Plataforma para gerar ebooks infantis personalizados: o usuario envia a foto da crianca, escolhe uma historia pronta e recebe um PDF ilustrado. Apos o ebook, tambem e possivel gerar **animacao** (1 clipe Kling) e **video narrado** (Kling por cena + TTS + ffmpeg; sem `KLING_*` cai em Ken Burns).

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
Com `KLING_API_KEY` (chave unica `api-key-kling-...` do console novo) ou `KLING_ACCESS_KEY` + `KLING_SECRET_KEY` (JWT antigo), o video narrado anima ate 6 cenas via Kling image2video (personagem + fundo vivo). Sem Kling, usa Ken Burns nas paginas estaticas. Sem ffmpeg, cai em GIF slideshow (com edge-tts quando disponivel). Sem Kling, a animacao curta tambem gera GIF offline.

## Fluxo

1. Criar conta / entrar
2. Informar nome, idade, genero e foto da crianca
3. Escolher uma das historias do catalogo e a faixa etaria do texto (automatica pela idade ou manual: 2-5, 5-9, 6-9, 9-12)
4. Aguardar geracao (personagem -> cenas -> PDF)
5. Baixar o ebook
6. (Opcional) Gerar animacao e/ou video narrado na tela de resultado

## Stack

React (Vite) / FastAPI / Postgres / Redis / MinIO / Gemini (imagens) / ReportLab (PDF) / Kling (animacao + narrado animado) / edge-tts ou ElevenLabs + ffmpeg
