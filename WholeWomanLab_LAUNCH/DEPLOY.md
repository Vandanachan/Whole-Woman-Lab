# WholeWomanLab — Deployment Checklist (for the developer)

The code is finished and tested. This is a **deploy-only** task: publish the
Python backend, publish the static frontend, connect them, lock CORS. Estimated
time: ~30–45 minutes. No application code needs to be written.

Contents of this package:
- `backend/`  — FastAPI service + vendored reasoning engine + `Dockerfile` + `.do/app.yaml`
- `frontend/` — single static `index.html`

Client priority: **privacy + India data residency.** Deploy the backend in an
**India region**. The app is **stateless** (stores nothing) — keep it that way.

---

## 1. Backend → DigitalOcean App Platform (Bangalore / BLR)

Recommended because it offers an India region and a BAA/DPA path.

1. Create a DigitalOcean account; sign the DPA (and BAA if any US-medical use).
2. Push `backend/` to a Git repo (GitHub/GitLab), **or** use `doctl apps create`.
3. Create an App from the repo; DO will detect `backend/Dockerfile` and
   `backend/.do/app.yaml`. Confirm **region = BLR (Bangalore)** and the
   `basic-xxs` instance.
4. Deploy. Confirm `GET https://<app-url>/health` returns
   `{"status":"ok", ...}` and `GET /docs` loads.

_Alternative host (Render):_ New → Web Service → Docker → root `backend/`,
start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, region Singapore.
Note: Render does not sign BAAs — only use if the app stays stateless.

## 2. Frontend → Netlify (static)

1. Drag `frontend/index.html` onto https://app.netlify.com/drop (or connect the
   repo). You get a URL like `https://<name>.netlify.app`.
2. Open it, paste the **backend URL from step 1** into the "Backend API" box,
   click **Connect**. Verify the questions load, a reading generates, and the
   PDF downloads.

## 3. Lock CORS (do this after the frontend URL is known)

In `backend/app/main.py`, change:

```python
allow_origins=["*"]
```
to the exact frontend origin, e.g.:
```python
allow_origins=["https://<name>.netlify.app"]
```
Redeploy the backend.

## 4. Handover checklist

- [ ] Backend deployed in **Bangalore**, `/health` green
- [ ] Frontend live on Netlify, pointed at the backend URL
- [ ] Full loop works: questions → reading → **PDF downloads**
- [ ] CORS restricted to the frontend origin, backend redeployed
- [ ] Both on HTTPS (automatic on DO + Netlify)
- [ ] DPA signed with the host; app confirmed **stateless** (no DB)
- [ ] Give the owner: the two URLs + the DO/Netlify login details

## 5. Tests (optional sanity check)

```bash
cd backend && pip install -r requirements.txt && pytest -q   # 6 tests pass
```
