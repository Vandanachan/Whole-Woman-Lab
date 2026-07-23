# WholeWomanLab — Frontend (static web page)

A single self-contained `index.html` — no build step, no framework. It talks to
your backend API, renders the intake questionnaire, shows the reading on screen,
and downloads the generated PDF. Host it on any static web host.

## What it does

1. On load it calls `GET {API}/questions` and renders the checklists.
2. The practitioner ticks findings + fills client info.
3. **Generate reading** → `POST {API}/diagnose` → shows the structured reading.
4. **Download PDF report** → `POST {API}/report/pdf` → downloads the PDF.

The **Backend API** box at the top is where you paste your backend's URL; it is
remembered in the browser for next time. "Load sample case" pre-fills a demo so
you can test instantly.

## Try it locally (with the backend running)

```bash
# 1) start the backend (in the backend/ folder)
uvicorn app.main:app --reload --port 8000

# 2) serve this folder (any static server works)
cd frontend
python3 -m http.server 8090
# open http://localhost:8090  ->  set API to http://localhost:8000  ->  Connect
```

## Host it on a web page (no server for the frontend)

The frontend is just one file, so any static host works — free tiers are fine:

* **Netlify Drop** — drag `index.html` onto <https://app.netlify.com/drop>; you get a public URL in seconds.
* **GitHub Pages** — commit `index.html` to a repo, enable Pages.
* **Cloudflare Pages / Vercel** — point at the folder.

After hosting, open your page, paste your **deployed backend URL** into the
Backend API box, and Connect. (The backend must be deployed and reachable — see
`backend/README.md`.)

## Important for going live

* **CORS**: the backend currently allows all origins (`*`) for development. Once
  your frontend has a fixed URL, restrict `allow_origins` in `backend/app/main.py`
  to that URL.
* **HTTPS**: host both frontend and backend over HTTPS (all the hosts above do
  this automatically) so the browser doesn't block the API calls.
* **Health data**: add authentication and review privacy obligations before
  collecting real client data at scale.

## Customising

* **Branding**: edit the `--brand` colour and the header text at the top of `index.html`.
* **Questions**: they come from the backend automatically — add a finding to
  `backend/data/evidence.json` and it appears here with no frontend change.
