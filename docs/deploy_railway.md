# Deploying the Studio demo to Railway

The Studio (`studio.py`) runs the **semantic (hybrid) engine** live on pasted
résumés. No LLM, no GPU, no API keys — just a 90 MB MiniLM embedding model baked
into the image. Interactive memory is ~450 MB; the 100K "Proof at scale" tab is
served from a **pre-baked snapshot** so no visitor triggers a multi-GB live rank.

## What's in the repo for this

| File | Purpose |
|---|---|
| `Dockerfile.web` | Hosted image: installs CPU-only torch + sentence-transformers, **bakes the MiniLM model**, runs `studio.py`. |
| `.dockerignore` | Excludes the 146 MB index, the 465 MB organizer dataset, `.git`, tests — keeps the image lean. |
| `railway.json` | Points Railway at `Dockerfile.web`; health check on `/health`. |
| `outputs/challenge_prebaked.json` | The deterministic 100K result the "Proof at scale" tab serves on the host. Regenerate with `make prebake`. |
| `/health` route | Liveness probe (no engine work). |

`studio.py` reads `$PORT` and binds `0.0.0.0` automatically when `$PORT` is set,
so it works on Railway/Fly/any container host with no code change.

## Deploy (Railway CLI — you run these, they need your Railway login)

```bash
# 1. one-time: log in and link a project
railway login
railway init            # or: railway link   (to attach to an existing project)

# 2. make sure the 100K snapshot is fresh (only if the ranking changed)
make prebake

# 3. deploy — Railway builds Dockerfile.web and runs it
railway up

# 4. get the public URL
railway domain          # generates/prints the https URL
```

Railway injects `$PORT`; nothing else is required. `HF_HUB_OFFLINE=1` is set in
the image so there is no network access at request time.

## Test the image locally first (needs Docker running)

```bash
make web-local          # builds + runs on http://localhost:8888
# then open it, paste a JD + a couple of résumés, check every tab
```

## Fit on Railway Hobby ($5 credit ≈ 0.5 GB RAM/mo)

- Interactive paste-a-résumé loop: **~450 MB peak** (measured) — fits, but tight.
- The 100K tab is pre-baked, so it never spikes memory on the host.
- If memory is ever exceeded under load, the Studio **degrades gracefully to the
  spine (keyword) engine** rather than crashing — but for a controlled demo, 450 MB
  on Hobby is fine. If you want headroom, bump to the next Railway tier or Fly.io
  `shared-cpu-1x` (1 GB).

## Notes

- The image does **not** ship the 146 MB embedding index or the 100K dataset —
  the demo live-embeds small pastes and serves the 100K tab from the snapshot.
- Cold start includes loading MiniLM (~2–4 s on first request); it's cached after.
