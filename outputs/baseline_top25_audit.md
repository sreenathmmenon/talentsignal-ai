# Baseline Top-25 Audit

Generated from `outputs/baseline_submission.csv`.

## Summary

The baseline top 25 is directionally credible for an initial model: it is dominated by Senior Machine Learning Engineer, Senior NLP Engineer, AI Engineer, Lead AI Engineer, Search Engineer, Applied ML Engineer, and Recommendation Systems Engineer profiles. Reasoning references career evidence for BM25, ranking, retrieval, recommendation, matching, vector/search tools, production terms, and evaluation terms.

This is not a final human audit. It is the Epic 1-3 baseline audit confirming that the first valid ranker is not obviously broken and is suitable for deeper Epic 4-8 optimization.

## Passes

- Top 10 contains relevant AI/ML/search titles.
- Top 10 reasoning is grounded in extracted terms.
- No top-25 row has risk flags in `outputs/factor_scores.csv`.
- Scores are non-increasing and the official validator passes.
- Several candidates have preferred locations such as Noida, Pune, Hyderabad, Gurgaon, and Bangalore.

## Concerns To Address Later

- Some high-ranked candidates outside preferred India locations should be compared against slightly lower India-based candidates.
- Notice period concerns appear at ranks 7, 9, and 24; later scoring should verify whether these candidates deserve their exact rank.
- The baseline does not yet include a full manual raw-profile inspection for all top-25 candidates.
- The baseline uses deterministic evidence rules; future iterations should improve synonym coverage and candidate comparison.

## Next Action

Proceed to Epic 4+ only after preserving this baseline. Future scoring changes must rerun official validation and refresh this audit.

