# Evaluation Report — engine: `spine`

## Per-role ranking quality

Mean composite across roles: **0.8781**

| role | NDCG@10 | NDCG@50 | MAP | P@10 | composite |
|---|---|---|---|---|---|
| ai_search | 0.973 | 0.888 | 0.827 | 1.000 | 0.927 |
| sales | 0.973 | 0.851 | 0.782 | 1.000 | 0.909 |
| data_analytics | 0.856 | 0.649 | 0.477 | 0.700 | 0.729 |
| backend | 0.920 | 0.824 | 0.633 | 0.800 | 0.842 |
| product | 0.972 | 0.845 | 0.826 | 1.000 | 0.913 |
| design | 0.986 | 0.915 | 0.869 | 1.000 | 0.948 |

## Honeypot suite (must stay ~0 in top-10)

- honeypot_rate@10: **0.200**
- honeypot_rate@100: 0.781
- ndcg@10: 0.918

## Paraphrase suite (zero-keyword strong fits)

- paraphrase-ideal mean rank: **16.9** (of 10)
- paraphrase-ideal in top-10: 3
- ndcg@10: 0.541

## Perturbation suite

- strong rank: 1, paraphrase rank: 5, contradicted rank: 2
- contradicted ranked below strong: True

## Generality suite (cross-JD top-10 overlap — lower is better)

- mean pairwise Jaccard overlap: **0.058**
- max pairwise overlap: 0.25

## Schema-agnostic suite (non-Redrob signal vocabulary)

- ran without error: True
- ndcg@10: 0.946509999116795
