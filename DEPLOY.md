# Story2 — Deploy online

## Opcao A (recomendada): tudo no Render (1 URL)

1. Push deste repo no GitHub
2. Em [render.com](https://render.com) ? **New ? Blueprint** ? selecione o repo
3. Confirme o `render.yaml` (cria `story2-db` + `story2-api`)
4. Opcional: preencha `GEMINI_API_KEY` no painel (sem ela usa placeholders)
5. URL final: `https://story2-api.onrender.com`

O container sobe API + worker + frontend React.

## Opcao B: Vercel (front) + Render (API)

1. Backend no Render (Blueprint)
2. Frontend: `vercel --prod` na pasta Story2
3. Ajuste `vercel.json` se a URL da API for diferente de `story2-api.onrender.com`

## Variaveis

| Var | Default | Nota |
|---|---|---|
| `DATABASE_URL` | (Render) | Postgres do Blueprint |
| `STORAGE_BACKEND` | `local` | Sem R2 no free tier |
| `GEMINI_API_KEY` | vazio | Offline fallback se vazio |
| `JWT_SECRET` | gerado | Auth |
| `OFFLINE_FALLBACK` | true | Placeholders sem Gemini |
