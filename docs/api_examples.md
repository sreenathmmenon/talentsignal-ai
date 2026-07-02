# TalentSignal REST API — copy-paste examples

Base URL (local): `http://localhost:8900` · start with `python api_server.py`
Interactive docs: **`/docs`** (Swagger UI) · spec: `/openapi.json`

Auth is optional: set `TALENTSIGNAL_API_KEY` in the environment to require an
`X-API-Key` header on every request.

A Postman/Insomnia collection is at [`docs/talentsignal.postman_collection.json`](talentsignal.postman_collection.json)
— import it and hit **Send**.

---

## Rank candidates against a JD

```bash
curl -s localhost:8900/rank -H 'Content-Type: application/json' -d '{
  "jd": "Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years.",
  "candidates": [
    {"candidate_id":"CAND_0000001",
     "profile":{"current_title":"ML Engineer","years_of_experience":7,
                "summary":"Built embeddings-based retrieval and ranking in Python."},
     "career_history":[{"title":"ML Engineer","description":"Owned ranking + retrieval; shipped to production."}],
     "skills":["Python","Ranking","Embeddings"]}
  ],
  "top_n": 5
}'
```

Returns `{ job_title, engine, candidate_count, ranked: [ {rank, candidate_id, score,
title, reasoning, reachability_label, factors, requirement_matches, risk_flags} ] }`.

## Parse a JD into requirements

```bash
curl -s localhost:8900/ingest/jd -H 'Content-Type: application/json' \
  -d '{"jd":"Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."}'
```

## Parse a résumé into a profile

```bash
curl -s localhost:8900/ingest/resume -H 'Content-Type: application/json' \
  -d '{"resume":"Asha — ML Engineer, 7 yrs. Built ranking & retrieval. Skills: Python."}'
```

## Audit a candidate for fabrication / contradictions

```bash
curl -s localhost:8900/audit -H 'Content-Type: application/json' -d '{
  "candidate": {"candidate_id":"CAND_X",
    "skills":[{"name":"Embeddings","proficiency":"expert","months_used":0}],
    "career_history":[{"title":"AI Lead","duration_months":180}],
    "profile":{"years_of_experience":4}}
}'
```

Returns `{ is_impossible, penalty, flags: [{code, detail}] }` — the honeypot check
that catches keyword-stuffed / impossible résumés.

## Adverse-impact (four-fifths) compliance on a ranking

Group labels come from **your** HR data; the engine never infers protected attributes.

```bash
curl -s localhost:8900/compliance -H 'Content-Type: application/json' -d '{
  "ranked_ids": ["CAND_1","CAND_2","CAND_3","CAND_4"],
  "group_attributes": {"gender": {"CAND_1":"F","CAND_2":"M","CAND_3":"F","CAND_4":"M"}},
  "top_k": 2
}'
```

## Candidate-facing transparency report

```bash
curl -s localhost:8900/candidate_report -H 'Content-Type: application/json' -d '{
  "candidate": {"candidate_id":"CAND_0000001","profile":{"summary":"Built ranking and retrieval."},"skills":["Python"]},
  "jd": "Senior AI Engineer. Must have embeddings, retrieval, ranking, Python. 5-9 years."
}'
```

## Health

```bash
curl -s localhost:8900/health
```

---

### With an API key

```bash
export TALENTSIGNAL_API_KEY=your-secret          # server side
curl -s localhost:8900/rank -H 'X-API-Key: your-secret' -H 'Content-Type: application/json' -d '{...}'
```
