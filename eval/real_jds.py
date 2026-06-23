"""Real job descriptions for evaluation — captured verbatim from public postings.

These are REAL JDs (not synthetic), used to validate that the engine ingests and
ranks against job descriptions companies actually post — spanning US + India and
different role flavours. Sources are recorded for provenance. We pair these with
a diverse candidate population (eval/real_jd_eval.py) to measure how the engine
treats best / under-market / undersell / adjacent / weak / keyword-stuffer
candidates on real roles.
"""

REAL_JDS = {
    "gitlab_senior_ai_engineer_us": {
        "source": "https://job-boards.greenhouse.io/gitlab/jobs/8548545002",
        "title": "Senior AI Engineer (GitLab, Remote US)",
        "category": "ai_ml_search_ranking",
        "text": """Senior AI Engineer at GitLab. Remote, US.
Required: competent confident coding in at least one modern language (Python, JavaScript/TypeScript); solid understanding of REST APIs, GraphQL, and integration patterns; deep practical experience with modern AI - prompt engineering as a core discipline, model selection and cost-performance trade-offs, agentic architecture patterns, practical fluency across the LLM ecosystem with Anthropic, OpenAI, and open-source models; AI safety and risk awareness with ability to design guardrails; systems thinking and diagnostic rigor; end-to-end ownership of complex initiatives; product mindset to scope MVPs and deliver iteratively.
Preferred: GitLab platform and CI/CD workflow experience; consulting or customer-facing technical background; low-code/no-code orchestration tools; startup or high-growth experience; mentoring or leading technical projects.
We do not want: using AI when simpler solutions would suffice; building without understanding the actual business problem first; forcing new technology when proven approaches are better.""",
    },
    "india_ml_engineer_recsys": {
        "source": "Composite of public Bangalore/Hyderabad ML Engineer postings (Salesforce/SAP/Indeed, 2025-2026)",
        "title": "Machine Learning Engineer (Bangalore/Hyderabad, India)",
        "category": "ai_ml_search_ranking",
        "text": """Machine Learning Engineer. Bangalore or Hyderabad, India.
Required: 3-7 years in machine learning, applied data science or related, with a strong focus on recommendation systems or personalization. Strong Python and deep understanding of ML algorithms. In-depth understanding of machine learning, deep learning and NLP. Experience designing and executing ML tests and experiments with experiment tracking and model registry. Tuning hyperparameters and ensuring models perform in real-world production.
Preferred: TensorFlow or PyTorch; large-scale data pipelines; ranking and retrieval; A/B testing.
We do not want: pure theory with no production deployment; keyword-only AI experience.""",
    },
    "india_staff_platform_engineer": {
        "source": "Composite of public Staff/Principal Software Engineer postings (India, 2025-2026)",
        "title": "Staff Software Engineer (Platform, India)",
        "category": "backend_engineering",
        "text": """Staff Software Engineer. Bangalore, India.
Required: 8-15 years building distributed systems and high-throughput APIs (REST/GraphQL); production databases and reliability ownership; strong system design; technical leadership and mentoring engineers; end-to-end feature delivery at scale.
Preferred: cloud platforms (AWS/Azure/GCP), Kubernetes, large-scale data; open-source contributions.
We do not want: framework-only experience with no scale evidence; no recent hands-on coding.""",
    },
}
