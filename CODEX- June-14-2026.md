# CODEX- June-14-2026

## Redrob Hackathon Strategy Document

This is the current Codex understanding and strategy for the Redrob Intelligent Candidate Discovery and Ranking Challenge. Treat this as a living planning document while we gather additional plans from other providers and merge the strongest ideas.

## Goal

Win the hackathon, maximize the chance of first prize, and create a defensible engineering submission that can lead to direct hiring/interview opportunities from Redrob and other companies.

The submission should not look like a quick keyword-matching script. It should demonstrate product judgment, ranking-system thinking, explainability, reproducibility, and the ability to defend tradeoffs in an engineering interview.

We are not limiting development to any single tool or platform. Use whatever helps us build the best possible product and submission: Codex, Claude, ChatGPT, Gemini, API keys, Google Colab, local Mac, cloud machines, notebooks, Docker, Streamlit, custom web apps, or other systems. The only hard limits are the official final-ranking reproduction rules enforced by the challenge.

## Broader Product Aim

The provided Senior AI Engineer JD is the first priority because it is what the hackathon evaluates. However, the solution should be designed as a general hiring-intelligence product, not a one-off JD-specific script.

The product direction:

- Accept any job description and extract its role, category, seniority, must-have signals, nice-to-have signals, disqualifiers, location/work-mode needs, and hiring preferences.
- Rank candidates or resumes from many categories, not just AI/ML.
- Support 100 or more JDs by changing configuration/rubrics rather than rewriting code.
- Generate recruiter-facing explanations grounded in evidence.
- Provide a product/demo experience impressive enough to support job opportunities beyond this hackathon.

For competition scoring, every product choice must still prioritize the given Redrob Senior AI Engineer JD first.

## Challenge Understanding

Track 1 asks participants to build an intelligent AI-powered candidate ranking system. The system must rank candidates for a Senior AI Engineer founding-team role at Redrob AI.

The system should:

- Understand the job description deeply, not just match keywords.
- Rank candidates by actual role fit.
- Use candidate profile data, career history, skills, education, and Redrob behavioral signals.
- Produce a top-100 shortlist with scores and concise reasoning.
- Be explainable and reproducible under strict compute constraints.

The job description is intentionally nuanced. The target candidate is not simply someone with many AI keywords. The ideal profile is closer to:

- 5-9 years of experience, with flexibility for strong outliers.
- Applied AI/ML engineer with production systems experience.
- Direct evidence of retrieval, ranking, search, embeddings, vector/hybrid search, recommender systems, LLM systems, or evaluation infrastructure.
- Strong Python and production engineering judgment.
- Product-company or startup shipping experience.
- Preference for India, especially Pune, Noida, Delhi NCR, Mumbai, Hyderabad, Bangalore, or relocation willingness.
- Active and reachable candidate behavior.

## Available Assets

The local challenge bundle includes:

- `candidates.jsonl`: 100,000 candidate profiles.
- `sample_candidates.json`: small readable sample.
- `job_description.docx`: target Senior AI Engineer JD.
- `candidate_schema.json`: full candidate profile schema.
- `redrob_signals_doc.docx`: behavioral signal documentation.
- `submission_spec.docx`: submission rules and evaluation pipeline.
- `sample_submission.csv`: format example only, not a high-quality ranking.
- `validate_submission.py`: CSV format validator.
- `submission_metadata_template.yaml`: required metadata template.
- `Idea Submission Template _ Redrob.pdf`: structure for presentation/methodology.
- `challenge1.txt`: short challenge statement.

## Submission Requirements

Final submission must include:

- A CSV with exactly 100 candidate rows plus a header.
- Required columns in order: `candidate_id,rank,score,reasoning`.
- Unique ranks from 1 to 100.
- Unique candidate IDs.
- Scores monotonically non-increasing by rank.
- Grounded reasoning, ideally 1-2 sentences per candidate.
- GitHub repository with all code required to reproduce the CSV.
- README with exact reproduction command.
- Methodology document.
- Metadata YAML.
- Sandbox/demo link or Docker-based runnable alternative.

Recommended reproduce command:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

## Official Final-Ranking Constraints

These constraints are not restrictions on our research, development, demo, or tooling. They are the official challenge constraints for the final command that reproduces the submitted CSV:

- Runtime: 5 minutes or less.
- Memory: 16 GB RAM or less.
- Compute: CPU only.
- Network: off.
- No hosted LLM/API calls during ranking.
- No GPU during ranking.

Codex, Claude, ChatGPT, Gemini, API keys, Google Colab, cloud machines, Docker, Streamlit, notebooks, and other tools may be used during development, research, debugging, review, experiments, and demo building. That use must be declared honestly where required. The submitted ranking command itself must run offline without those services.

## Scoring And Evaluation

Hidden scoring weights:

- NDCG@10: 50%.
- NDCG@50: 30%.
- MAP: 15%.
- P@10: 5%.

This means top-10 quality matters most. A conservative, high-precision top 10 is more important than a broad list of 100 weak candidates.

Evaluation stages:

1. Format validation.
2. Hidden scoring.
3. Code reproduction under compute limits and honeypot check.
4. Manual review of reasoning, methodology, git history, and code quality.
5. Interview defense with Redrob engineering.

## Known Traps

The dataset intentionally contains traps. The ranker should naturally down-rank them.

Major risks:

- Candidates with many AI keywords but irrelevant titles/career paths.
- Non-technical candidates, such as Marketing Manager or HR Manager, with AI skill stuffing.
- Profiles that mention AI curiosity or ChatGPT usage but lack production ML experience.
- Pure research profiles without production deployment.
- Candidates focused mainly on computer vision, speech, or robotics without NLP/IR/retrieval relevance.
- Service-only careers where the JD explicitly raises concern.
- Stale candidates with low recent activity or poor recruiter response.
- Suspicious/impossible profiles, such as expert skills with zero duration.
- Candidates with perfect skills but low availability signals.

## Recommended Technical Strategy

Build a general JD-to-candidate ranking engine, then tune and validate it first against the Redrob Senior AI Engineer JD. The competition path should remain CPU-fast and explainable using structured features plus lightweight text similarity.

The ranker should parse each candidate and compute:

- Parsed JD requirements and category-specific scoring rubric.
- Career/domain fit.
- Applied ML/retrieval/ranking evidence.
- Seniority and logistics fit.
- Behavioral availability from Redrob signals.
- Lightweight semantic similarity against the JD.
- Suspicious-profile penalties.

Suggested scoring weights:

- 40% career/domain fit.
- 25% applied ML/retrieval/ranking evidence.
- 15% seniority/logistics.
- 15% Redrob behavioral availability.
- 5% semantic TF-IDF similarity.

Apply penalties after base score for suspicious profiles, stale availability, extreme title mismatch, service-only career risk, and unsupported AI keyword stuffing.

## Candidate Fit Rubric

High positive signals:

- Current or recent title: Senior AI Engineer, ML Engineer, Applied ML Engineer, Recommendation Systems Engineer, Search Engineer, Data Scientist, Backend Engineer with ML/search evidence, Senior Software Engineer (ML).
- Career descriptions mention production ranking, retrieval, search, recommendation, embeddings, vector search, hybrid search, evaluation metrics, A/B testing, or user-facing ML systems.
- Skills include Python, NLP, embeddings, RAG, vector databases, FAISS, Elasticsearch/OpenSearch, Qdrant, Milvus, Pinecone, Weaviate, ML evaluation, LLM fine-tuning, LoRA/QLoRA/PEFT.
- Product-company or startup experience.
- Experience roughly 5-9 years.
- India-based, especially Pune/Noida/Delhi NCR/Mumbai/Hyderabad/Bangalore, or willing to relocate.
- Active recently, open to work, verified, responsive, reasonable notice period.

Strong negative signals:

- Current title is unrelated and career history does not support an AI engineering transition.
- Only generic AI-tool usage or recent ChatGPT productivity experimentation.
- Long stale activity and very low recruiter response rate.
- Service-only career with no product-company evidence.
- Excessive keyword list with weak duration/endorsement/assessment support.
- No production deployment evidence.

## Explainability Strategy

Reasoning must be grounded in facts extracted from the profile.

Good reasoning should mention:

- Candidate title and years of experience.
- Specific relevant skills or systems.
- Career evidence connected to the JD.
- Behavioral/logistics signal where useful.
- Honest concern if rank is lower or there is a tradeoff.

Avoid:

- Hallucinated skills or employers.
- Generic praise.
- Identical templated sentences.
- Reasoning that sounds stronger than the assigned rank.

## Deliverables To Build

Core repo:

- `rank.py`: main offline ranking command.
- `jd_parser.py`: extracts configurable hiring criteria from a JD.
- `features.py`: candidate parsing and feature extraction.
- `scoring.py`: scoring rubric and penalties.
- `reasoning.py`: grounded reason generation.
- `validate.py` or documented validator command.
- `tests/`: focused tests for feature extraction, score ordering, CSV validity, and no-hallucination reasoning.
- `README.md`: setup and reproduction instructions.
- `methodology.md`: approach explanation for reviewers.
- `submission_metadata.yaml`: filled from template.
- Demo/product UI in the best available platform. Streamlit, Docker, Colab, a custom web app, or another option are all acceptable if they showcase the system well.

## Development Plan

1. Read all bundle docs and convert key `.docx`/PDF content into local notes.
2. Build a baseline parser and profile summarizer.
3. Implement the scoring rubric.
4. Generate a first top-100 CSV.
5. Manually inspect top 25 and tune obvious false positives.
6. Add suspicious-profile checks.
7. Improve reasoning generator.
8. Validate CSV using provided validator.
9. Benchmark full runtime and memory.
10. Write methodology and README.
11. Build and test sandbox/demo.
12. Make final submission after one last manual top-25 audit.

## How To Use Other Providers

Ask other providers to improve this plan in specific ways:

- Strengthen the general product architecture for ranking candidates across many JDs and categories.
- Propose better scoring weights.
- Identify additional trap patterns.
- Suggest stronger feature engineering for hidden NDCG@10.
- Review the JD and derive must-have vs nice-to-have signals.
- Improve explanation wording without hallucination.
- Suggest validation and demo improvements.
- Prepare interview-defense questions and answers.

Make clear to providers: tools are not restricted during development. Use the strongest available methods. The only place live API calls, network, GPU, and cloud dependencies are forbidden is the final challenge reproduction command.

## Current Defaults

- Timeline: 3-7 days.
- Development: any useful tool, platform, cloud, AI assistant, notebook, API, or demo stack.
- Final challenge reproduction command: CPU-only, no network, no GPU, within official limits.
- Demo: choose the platform that best presents the product; Streamlit, Docker, Colab, or a custom app are all options.
- Main optimization target: top-10 precision, then top-50 quality.
- Product ambition: support many JDs and categories, with the provided Redrob JD as first-priority validation.
