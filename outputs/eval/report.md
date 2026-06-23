# Evaluation Report — engine: `hybrid`

## Per-role ranking quality

Mean composite across roles: **0.954**

| role | NDCG@10 | NDCG@50 | MAP | P@10 | composite |
|---|---|---|---|---|---|
| ai_search | 0.945 | 0.972 | 0.972 | 1.000 | 0.960 |
| sales | 0.973 | 0.976 | 0.899 | 1.000 | 0.964 |
| data_analytics | 0.973 | 0.947 | 0.891 | 1.000 | 0.955 |
| backend | 0.973 | 0.872 | 0.814 | 1.000 | 0.920 |
| product | 0.973 | 0.948 | 0.848 | 1.000 | 0.948 |
| design | 1.000 | 0.986 | 0.870 | 1.000 | 0.976 |

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

- mean pairwise Jaccard overlap: **0.065**
- max pairwise overlap: 0.429

## Schema-agnostic suite (non-Redrob signal vocabulary)

- ran without error: True
- ndcg@10: 0.9733323042090073
