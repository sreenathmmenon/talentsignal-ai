# Project Iteration Rule

Current working deadline assumption: June 30, 2026.

The project is not considered finished merely because a valid package exists. The current repository state is a validated checkpoint. We will keep discussing, reviewing, auditing, improving, testing, and validating until the final chosen submission moment.

## No Submission Yet

Do not treat the current package as uploaded or final-submitted.

The current state is:

- locally validated,
- pushed to GitHub,
- reproducible,
- live REST-backed UI checkpoint validated by Playwright against real challenge data,
- ready for further iteration.

It is not a final frozen submission state. The current UI is no longer a static checkpoint; it is a live recruiter cockpit served by `app.py` with `/api/rank` and `/download/...`. Continue iterating for final product polish, hosted deployment, broader manual review, and final freeze.

## Completion Standard Still Applies

`PROJECT_COMPLETION_RULE.md` remains the controlling rule.

Any future story, feature, audit, UI, backend change, ranker change, documentation update, or final submission artifact is complete only when it works end to end, is tested, validated, reviewed, and has no known unresolved critical issue.

## Iteration Priorities

Before final submission, continue improving:

- production-grade interactive UI/demo polish,
- hosted deployment or recorded demo path,
- raw-profile manual audit quality,
- top-10 and top-50 ranking quality,
- scoring weights and trap handling,
- explanation quality,
- demo/product polish,
- methodology clarity,
- interview defense,
- clean reproduction,
- final submission checklist.

## Final Freeze Rule

Only freeze the final submission when:

- Sreenath explicitly says to prepare the final submission,
- the final CSV is regenerated,
- all validators pass,
- the top candidates are manually audited,
- the demo/docs/metadata are current,
- the completion rule is satisfied again after the final changes.
