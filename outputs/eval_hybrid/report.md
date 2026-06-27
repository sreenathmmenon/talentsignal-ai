# Evaluation Report — engine: `hybrid`

## Per-role ranking quality

Mean composite across roles: **0.9728**

| role | NDCG@10 | NDCG@50 | MAP | P@10 | composite |
|---|---|---|---|---|---|
| ai_search | 0.966 | 0.987 | 1.000 | 1.000 | 0.979 |
| sales | 0.945 | 0.960 | 0.918 | 1.000 | 0.948 |
| data_analytics | 0.971 | 0.989 | 0.998 | 1.000 | 0.982 |
| backend | 0.973 | 0.980 | 1.000 | 1.000 | 0.981 |
| product | 0.973 | 0.987 | 0.945 | 1.000 | 0.975 |
| design | 0.973 | 0.989 | 0.928 | 1.000 | 0.973 |

## Honeypot suite (must stay ~0 in top-10)

- honeypot_rate@10: **0.000**
- honeypot_rate@100: 0.781
- ndcg@10: 1.000

## Paraphrase suite (zero-keyword strong fits)

- paraphrase-ideal mean rank: **5.5** (of 10)
- paraphrase-ideal in top-10: 10
- ndcg@10: 1.000

## Perturbation suite

- strong rank: 1, paraphrase rank: 2, contradicted rank: 43
- contradicted ranked below strong: True

## Generality suite (cross-JD top-10 overlap — lower is better)

- mean pairwise Jaccard overlap: **0.056**
- max pairwise overlap: 0.429

## Schema-agnostic suite (non-Redrob signal vocabulary)

- ran without error: True
- ndcg@10: 0.9733323042090073
