"""Free-text + structured JD library, one entry per role.

Each role has:
  * a free-text JD (`text`) written the way a real hiring manager would — used to
    exercise the free-text JD ingestion path (Story 3) and the demo.
  * a structured spec path (`spec_path`) — the existing YAML scorecard, the
    always-works fallback the loader already understands.

Keeping both proves the product accepts ANY JD format, and lets the eval suite
compare "ingested free text" against "hand-written scorecard" for the same role.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JDEntry:
    role_id: str
    title: str
    spec_path: str
    text: str


AI_SEARCH_JD = """\
Senior AI Engineer — Founding Team

We are building the intelligence layer of a talent platform and need someone who
has actually shipped retrieval and ranking systems to real users. You will own
how candidates are matched to roles: the embeddings, the hybrid retrieval, the
ranking model, and the evaluation that tells us whether any of it works.

You must have production experience with embeddings-based retrieval (sentence
transformers, BGE, E5, or similar) and with a vector or hybrid search system
(FAISS, Qdrant, Elasticsearch, OpenSearch). Strong Python is required. You must
have designed evaluation frameworks for ranking — NDCG, MRR, MAP, offline-to-
online correlation, A/B testing. We care that you've handled embedding drift,
index refresh, and retrieval-quality regressions in production.

Nice to have: LLM fine-tuning (LoRA/QLoRA/PEFT), learning-to-rank models, prior
HR-tech or marketplace experience, open-source or published work.

We will not move forward with: pure research backgrounds with no production
deployment; "AI experience" that is only recent LangChain-on-OpenAI demos;
people who haven't written production code in over a year; careers entirely at
services companies with no product evidence; computer-vision/speech/robotics
specialists with no NLP or retrieval exposure.

5-9 years of experience, ideally 6-8 with 4-5 in applied ML at product
companies. Based in or willing to relocate to Pune or Noida.
"""

SALES_JD = """\
Enterprise Account Executive

We're hiring an enterprise account executive to own a quota and close six-figure
SaaS deals. You must have carried an enterprise quota, generated your own
pipeline, and kept disciplined CRM hygiene. Experience selling to a B2B
technology buyer is required, with a track record of exceeding quota.

Nice to have: HR-tech or recruiting-software sales, large-deal negotiation,
strong outbound prospecting.

We will not move forward with: lead-generation-only backgrounds, candidates with
no quota ownership, or the wrong segment motion (pure SMB transactional sellers).

4-9 years in enterprise sales. Mumbai, Bangalore, or Delhi.
"""

DATA_JD = """\
Data Analytics Lead

You will define how the business measures success and use experimentation to
drive product decisions. Must have strong SQL, metric-definition ownership,
experimentation and causal thinking, and a record of dashboards that led to real
stakeholder decisions. You must own data quality.

Nice to have: marketplace analytics, pricing or growth analytics, experimentation
platforms.

We will not move forward with: dashboard-only work with no decision impact, tool
keywords without metrics ownership, or no business-stakeholder evidence.

5-10 years. Bangalore, Mumbai, or Gurgaon.
"""

BACKEND_JD = """\
Senior Backend / Platform Engineer

Own the distributed systems and high-throughput APIs that keep the product
running. Must have production experience with distributed systems, databases,
and message queues at scale, plus reliability and on-call ownership. Strong
system-design ability is required.

Nice to have: large-scale inference or data-platform work, open-source
contributions.

We will not move forward with: framework-only experience with no scale evidence,
or support-only implementation roles.

5-10 years. Bangalore, Hyderabad, or Pune.
"""

PRODUCT_JD = """\
Senior Product Manager (Growth)

Lead product discovery and ship features that move core metrics. Must have
launched customer-facing products end to end, owned a roadmap, and driven
cross-functional delivery with measurable business outcomes.

Nice to have: growth or marketplace product experience, strong data fluency.

We will not move forward with: project-coordination-only backgrounds with no
shipped product, or weak metrics ownership.

5-10 years. Bangalore, Gurgaon, or Mumbai.
"""

DESIGN_JD = """\
Senior Product Designer (Systems)

Own end-to-end product design and a design system. Must have shipped usable,
validated interfaces, run user research and usability testing, and built or
maintained a design system.

Nice to have: design-systems leadership, front-end literacy.

We will not move forward with: visual-only portfolios with no product impact, or
template portfolios with no shipped work.

5-10 years. Bangalore, Pune, or Remote.
"""

JDS = {
    "ai_search": JDEntry("ai_search", "Senior AI Engineer", "job_specs/redrob_senior_ai_engineer.yaml", AI_SEARCH_JD),
    "sales": JDEntry("sales", "Enterprise Account Executive", "job_specs/examples/enterprise_account_executive.yaml", SALES_JD),
    "data_analytics": JDEntry("data_analytics", "Data Analytics Lead", "job_specs/examples/data_analytics_lead.yaml", DATA_JD),
    "backend": JDEntry("backend", "Senior Backend Engineer", "job_specs/examples/backend_platform_engineer.yaml", BACKEND_JD),
    "product": JDEntry("product", "Senior Product Manager", "job_specs/examples/product_manager_growth.yaml", PRODUCT_JD),
    "design": JDEntry("design", "Senior Product Designer", "job_specs/examples/product_designer_systems.yaml", DESIGN_JD),
}
