# Deployment guide

This monorepo deploys in two pieces:

| Component | Hosted on            | Source dir   |
| --------- | -------------------- | ------------ |
| Backend   | HuggingFace Spaces   | `backend/`   |
| Frontend  | Vercel               | `frontend/`  |

The frontend (Vercel) calls the backend (HF) via the `VITE_API_URL` env var.
Faculty profile photos are served by the backend at `/staff-photos/<id>.jpg`.

---

## 1. Deploy the backend on HuggingFace Spaces

HF Spaces require `Dockerfile` and `README.md` at the **root** of the Space's
git repo. So the Space is its own repo, populated from this monorepo's
`backend/` folder.

### One-time setup

1. Create a new Space at https://huggingface.co/new-space:
   - **Owner:** your HF username
   - **Space name:** e.g. `sastra-research-finder`
   - **License:** MIT
   - **SDK:** **Docker** → **Blank**
   - **Visibility:** Public (or Private)
2. Clone the empty Space locally:
   ```bash
   git clone https://huggingface.co/spaces/<your-user>/sastra-research-finder hf-space
   ```
3. Copy the contents of `backend/` into the cloned Space folder:
   ```bash
   cp -r backend/. hf-space/
   cd hf-space
   git add .
   git commit -m "Initial backend deploy"
   git push
   ```
   First push uploads ~180 MB (photos + caches). Files >10 MB will auto-use
   git-LFS; HF will print instructions if you need to enable it.

### Configure secrets/variables on the Space

Go to **Settings → Variables and secrets** and add:

| Key                  | Type     | Value                                                                                       |
| -------------------- | -------- | ------------------------------------------------------------------------------------------- |
| `BACKEND_PUBLIC_URL` | Variable | `https://<your-user>-sastra-research-finder.hf.space`                                       |
| `CORS_ORIGINS`       | Variable | `https://<your-vercel-project>.vercel.app,http://localhost:5173,http://localhost:3000`      |
| `MISTRAL_API_KEY`    | Secret   | (optional) for RAG endpoints                                                                |
| `EXA_API_KEY`        | Secret   | (optional) for Exa web search                                                               |

After saving, the Space rebuilds automatically. First build is ~5-8 min
(installing `faiss-cpu`, `sentence-transformers`, copying photos).

### Verify

- Visit `https://<your-user>-sastra-research-finder.hf.space/health` — should
  return `{"status":"healthy",...}`.
- Visit `https://<your-user>-sastra-research-finder.hf.space/docs` — Swagger UI.
- Visit `https://<your-user>-sastra-research-finder.hf.space/staff-photos/C007.jpg`
  — should return a faculty photo.

---

## 2. Deploy the frontend on Vercel

1. Go to https://vercel.com/new and import the GitHub repo.
2. **Root Directory:** `frontend`
3. **Framework preset:** Vite (auto-detected).
4. **Environment variables** — add:
   - `VITE_API_URL` = `https://<your-user>-sastra-research-finder.hf.space/api`
5. Click **Deploy**.

After deploy, copy the `*.vercel.app` URL and add it to the HF Space's
`CORS_ORIGINS` variable (then redeploy the Space).

---

## 3. Local development

Two terminals:

```bash
# Terminal 1 — backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

```bash
# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Vite proxies `/api` and `/staff-photos` to the
backend on :8000.
