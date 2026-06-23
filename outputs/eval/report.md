# Evaluation Report — engine: `spine`

## Per-role ranking quality

Mean composite across roles: **0.8778**

| role | NDCG@10 | NDCG@50 | MAP | P@10 | composite |
|---|---|---|---|---|---|
| ai_search | 0.934 | 0.885 | 0.813 | 0.900 | 0.900 |
| sales | 0.987 | 0.853 | 0.781 | 1.000 | 0.916 |
| data_analytics | 0.851 | 0.677 | 0.496 | 0.700 | 0.738 |
| backend | 0.920 | 0.824 | 0.633 | 0.800 | 0.842 |
| product | 0.972 | 0.845 | 0.826 | 1.000 | 0.913 |
| design | 1.000 | 0.932 | 0.854 | 1.000 | 0.958 |

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
