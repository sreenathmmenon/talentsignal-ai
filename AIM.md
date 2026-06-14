# AIM: Redrob Hackathon Candidate Ranking

This document is a provider-neutral briefing for AI assistants, reviewers, collaborators, and planning tools. Use it to understand the challenge, our target, what assets we have, and what kind of solution we need.

## Primary Aim

We want to win the Redrob hackathon, target first prize, and maximize the chance of direct hiring or interview opportunities from Redrob and other companies.

The goal is not just to submit a working model. The goal is to create a high-quality, impressive, reproducible, explainable candidate ranking product that can be defended in a technical interview and shown as serious hiring-tech work.

Use whatever tools, platforms, APIs, AI assistants, cloud machines, notebooks, demos, UI frameworks, Docker setups, or hosting options are useful during development. Do not assume the team is restricting development to any single tool. The only non-negotiable limits are the official challenge reproduction rules for the final ranking command.

## Broader Product Aim

The challenge JD is the first priority because it is what the judges will score. However, the product should be designed as a general hiring-intelligence system, not a one-off script.

The intended product should eventually support:

- Ranking candidates for 100 or more job descriptions.
- Job descriptions from any category, not only AI/ML roles.
- Any resume or candidate-profile format that can be parsed into structured evidence.
- Recruiter-facing explanations and auditability.
- Configurable scoring rubrics per JD and company preference.
- Candidate shortlisting, screening, and hiring workflow support.

For this hackathon, the Redrob Senior AI Engineer JD remains the reference case and first validation target. Generality should strengthen the submission, but it must not weaken performance on the provided JD.

## Challenge

Build an intelligent AI-powered candidate ranking system for a Senior AI Engineer founding-team role at Redrob AI.

The system receives a large candidate dataset and one job description. It must output the best 100 candidates, ranked from strongest fit to weakest fit, with scores and reasoning.

The challenge explicitly warns that keyword filtering is not enough. A winning system should understand what the JD means, not only what words appear in it.

## What We Have

Local files and challenge materials:

- `challenge1.txt`: short challenge description.
- `Idea Submission Template _ Redrob.pdf`: template for idea/methodology presentation.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl`: 100,000 candidate profiles.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/sample_candidates.json`: sample candidate records.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx`: target job description.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidate_schema.json`: schema for candidates.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/redrob_signals_doc.docx`: behavioral signal reference.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/submission_spec.docx`: rules, scoring, constraints, and evaluation stages.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/sample_submission.csv`: CSV format example.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py`: submission validator.
- `[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/submission_metadata_template.yaml`: metadata template.

Planning documents created from this brief:

- `PROJECT_COMPLETION_RULE.md`: project-wide rule for when work can be called complete.
- `PROJECT_AUTHORSHIP_RULE.md`: project-wide authorship and no-coauthor rule.
- `CODEX- June-14-2026.md`: Codex strategy document.
- `WORLD_CLASS_EXECUTION_PLAN.md`: full build plan, architecture, and step-by-step execution path.
- `FIRST_PRIZE_PREMORTEM.md`: 200+ failure modes and countermeasures for why we might not win first prize.
- `AGENTIC_AI_TALENT_INTELLIGENCE_RESEARCH.md`: public market research, papers, product patterns, legal/IP guardrails, and revised agentic strategy.
- `PROJECT_EXECUTION_STORIES_AND_TASKS.md`: executable epics, user stories, tasks, priorities, dependencies, milestones, and day-by-day delivery plan.

## Job Description Understanding

Target role: Senior AI Engineer, founding team, Redrob AI.

Important JD signals:

- Deep technical depth in modern ML systems.
- Experience with embeddings, retrieval, ranking, search, LLMs, and fine-tuning.
- Production experience, not only research or demos.
- Product-engineering attitude and ability to ship practical systems.
- Strong Python.
- Experience with vector databases or hybrid search infrastructure.
- Experience with ranking evaluation: NDCG, MRR, MAP, offline/online evaluation, A/B testing.
- Prefer 5-9 years of experience, but strong outliers may qualify.
- Pune/Noida preferred; broader India locations and relocation are relevant.
- Active candidate availability matters.

Important negative JD signals:

- Pure research without production deployment.
- Only recent LangChain/OpenAI demo experience.
- Senior people who have stopped writing production code.
- Title-chasing job-hopping pattern.
- Consulting/service-only background without product-company evidence.
- Computer vision, speech, or robotics focus without significant NLP/IR/search/retrieval relevance.

## Submission Requirements

Output CSV must have:

```text
candidate_id,rank,score,reasoning
```

Rules:

- Exactly 100 data rows.
- Ranks must be exactly 1 through 100.
- Candidate IDs must be unique and valid.
- Scores must be non-increasing by rank.
- Reasoning is optional by format but strongly recommended for manual review.
- Reasoning must be factual, specific, varied, and grounded in the candidate profile.

Other required submission assets:

- GitHub repository.
- Code that reproduces the CSV.
- Methodology document.
- Metadata YAML.
- Sandbox/demo link, or a Docker-based runnable alternative.

## Official Final-Ranking Constraints

These are not our development restrictions. They are the official challenge constraints for the submitted ranking command that reproduces the final CSV:

- Run in 5 minutes or less.
- Use 16 GB RAM or less.
- Run on CPU only.
- Make no network calls.
- Use no GPU.
- Call no hosted LLM/API services.

AI tools, API keys, cloud services, Google Colab, notebooks, hosted models, custom UIs, Streamlit, Docker, and any other useful tools can be used during research, planning, experimentation, debugging, documentation, demo building, and product development. The final reproducible command submitted for scoring must still obey the official rules above.

## Evaluation

Hidden scoring:

- NDCG@10: 50%.
- NDCG@50: 30%.
- MAP: 15%.
- P@10: 5%.

Implication: top-10 precision is the highest priority. The ranker should be conservative and avoid flashy but risky candidates in the top 10.

Evaluation stages:

1. Format validation.
2. Hidden ranking score.
3. Code reproduction and honeypot check.
4. Manual review of reasoning, methodology, code quality, and git history.
5. Defend-your-work interview.

## Dataset Signals

Each candidate includes:

- Profile: headline, summary, location, country, years of experience, current title/company/industry.
- Career history: companies, titles, dates, industries, descriptions.
- Education.
- Skills: name, proficiency, endorsements, duration.
- Certifications and languages.
- Redrob behavioral signals.

Important Redrob signals:

- Profile completeness.
- Signup date and last active date.
- Open-to-work flag.
- Recruiter response rate.
- Average response time.
- Skill assessment scores.
- Notice period.
- Preferred work mode.
- Willingness to relocate.
- GitHub activity score.
- Search appearances.
- Saved by recruiters.
- Interview completion rate.
- Offer acceptance rate.
- Email/phone/LinkedIn verification.

## Known Traps

The dataset includes trap profiles and honeypots.

Avoid ranking candidates highly just because they contain AI keywords. Watch for:

- Marketing/HR/accounting/non-tech candidates with many AI skills.
- Profiles with generic ChatGPT or AI-curiosity language.
- Skill stuffing with weak duration or endorsements.
- Impossible profiles, such as expert skills with zero usage.
- Stale candidates with low response rate.
- Pure research candidates without production deployment.
- Service-only candidates when the JD prefers product/startup experience.
- Candidates with all the right terms but no real career evidence of ranking/retrieval/search/ML systems.

## Recommended Solution Direction

Build a general JD-to-candidate ranking engine, then tune and validate it first against the Redrob Senior AI Engineer JD. The core should be a CPU-fast, explainable hybrid ranker:

- Structured feature extraction from profile, career history, skills, and behavioral signals.
- JD parser that extracts role, seniority, must-have skills, nice-to-have skills, domain, location, work mode, disqualifiers, and culture/logistics signals.
- Lightweight text similarity against the JD.
- Explicit scoring rubric for JD-fit signals, configurable per role/category.
- Behavioral availability modifier.
- Suspicious-profile penalties.
- Deterministic ranking and deterministic tie-breaks.
- Grounded reasoning generator using only extracted facts.

Suggested scoring components:

- Career/domain fit: 40%.
- Applied ML/search/retrieval/ranking evidence: 25%.
- Seniority and logistics: 15%.
- Behavioral availability: 15%.
- Semantic text similarity: 5%.

Then apply penalties for trap patterns and profile inconsistency.

## What A Great Top Candidate Looks Like

A very strong candidate likely has:

- AI/ML/search/recommendation/ranking-related current or recent title.
- 5-9 years of experience, or a strong justified outlier.
- Evidence of production search, ranking, retrieval, recommender, embeddings, vector/hybrid search, or evaluation systems.
- Product-company/startup shipping experience.
- Strong Python and modern ML tooling.
- India location or relocation fit.
- Open to work, recently active, verified, responsive, reasonable notice period.
- Reasonable salary/logistics.

## What We Need From Other Providers

When feeding this to another provider, ask for:

- Ways to make this a general hiring product while still maximizing the current Redrob JD score.
- A better scoring rubric.
- Better trap/honeypot detection ideas.
- Better feature engineering ideas.
- A top-10 precision strategy.
- A grounded reasoning strategy.
- A methodology/presentation angle that judges will respect.
- A reproducibility and sandbox plan.
- Interview-defense preparation.

Important instruction for providers: do not treat tools like Streamlit, Google Colab, Docker, APIs, or cloud platforms as forbidden. They are allowed for development and demos. Only the final challenge reproduction command has the official CPU/no-network/no-GPU constraints.

## Desired Final Output

The final project should include:

- `rank.py` with one-command reproducibility.
- Valid final CSV.
- General JD-ranking architecture that can accept other JDs beyond the hackathon reference JD.
- Methodology document.
- README with setup and reproduction.
- Metadata YAML.
- Tests and validation.
- Runtime benchmark.
- Demo/sandbox in whichever platform best showcases the product.
- Clean git history showing real iteration.

## Current Strategic Priority

Optimize for NDCG@10. That means:

- Manually audit top 25 before final submission.
- Keep top 10 conservative and high-confidence.
- Avoid keyword-stuffing traps.
- Prefer real production evidence over skill-list matching.
- Make every explanation defensible.
