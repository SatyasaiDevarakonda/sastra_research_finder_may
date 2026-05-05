---
title: SASTRA Research Finder
emoji: 🔬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# SASTRA Research Finder — Backend

FastAPI backend for the SASTRA Research Finder. Indexes ~25K publications,
matches authors to current SASTRA faculty, and exposes search / analytics /
thematic / RAG endpoints.

## Deploying to HuggingFace Spaces

This backend is designed to be deployed as a **Docker** Space. The `app_port`
in the YAML header above tells HF Spaces which port to route traffic to.

### Required secrets / variables

Set these in **Settings → Variables and secrets** on the Space:

| Key                  | Type     | Description                                                                       |
| -------------------- | -------- | --------------------------------------------------------------------------------- |
| `BACKEND_PUBLIC_URL` | Variable | Public URL of this Space, e.g. `https://<user>-<space>.hf.space`. Used to build absolute `/staff-photos/<id>.jpg` URLs that load from the Vercel frontend. |
| `CORS_ORIGINS`       | Variable | Comma-separated list, e.g. `https://your-frontend.vercel.app,http://localhost:5173`. |
| `MISTRAL_API_KEY`    | Secret   | Optional — enables RAG endpoints.                                                 |
| `EXA_API_KEY`        | Secret   | Optional — enables Exa-powered web search.                                        |

### Endpoints

- `GET /` — service info
- `GET /health` — health check (DB, search engine, FAISS, RAG status)
- `GET /docs` — interactive Swagger UI
- `GET /api/...` — application endpoints
- `GET /staff-photos/<staff_id>.jpg` — faculty profile photos

## Local development

```bash
cd backend
python -m venv venv
source venv/bin/activate          # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend will be at `http://localhost:8000`. The Vite dev server proxies `/api`
and `/staff-photos` to it.

## Data files

The repo includes the precomputed assets needed at startup:

- `data/SASTRA_Publications_2024-25.xlsx` — publications source
- `data/Faculty-List.xlsx` — current faculty roster
- `data/thematic_single_rankings_faculty.pkl` — precomputed thematic rankings
- `data/cache/faiss_index` + `preprocessed_data.pkl` — FAISS index & embeddings
- `data/staff-photos/<staff_id>.jpg` — 637 faculty profile photos
