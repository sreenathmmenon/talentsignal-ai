# Deploying the TalentSignal demo (the clickable link)

Get a live demo anyone can try in ~5 minutes. Pick one:

## Option A — Render (easiest, free tier)
1. Push this repo to GitHub.
2. On [render.com](https://render.com) → New → Blueprint → connect the repo.
3. Render reads `render.yaml` and builds `Dockerfile.demo`. Done — you get a public URL.

## Option B — Railway / Fly.io
Both auto-detect `Dockerfile.demo`. On Railway: New Project → Deploy from repo →
it builds the Dockerfile. On Fly: `fly launch --dockerfile Dockerfile.demo`.

## Option C — HuggingFace Spaces (Docker)
1. Create a new Space → SDK: **Docker**.
2. Push the repo; rename `Dockerfile.demo` → `Dockerfile` in the Space (Spaces
   expects that name), or set the Dockerfile path.
3. The Space serves the UI on its public URL.

## Option D — local Docker (test the image first)
```bash
docker build -f Dockerfile.demo -t talentsignal-demo .
docker run -p 8800:8800 talentsignal-demo
# open http://localhost:8800
```

## What visitors see
Drop in a JD (paste or file) + resumes (PDF/DOCX/TXT/CSV/JSON/paste) → a live,
ranked, explainable shortlist with fit factors, matched requirements, risk flags,
grounded reasoning, and CSV export. The demo runs the hybrid engine on small
samples (live-embedded), with a clean spine fallback.

## Notes
- The demo image bundles the embedding model so it works after build.
- For the hackathon sandbox requirement, this same image / URL is the deliverable.
- The 100K challenge ranking uses the precomputed index (git-lfs), not the demo.
