"""RoleProfile library — the role-specific vocabulary that drives the synthetic
generator. Each role defines what a strong fit looks like (keyworded), what the
SAME fit looks like in paraphrase (zero shared keywords), and what adjacent /
weak / irrelevant / honeypot profiles contain.

Having several roles here is what proves the engine is JD-agnostic: the eval
suite ranks each role's pool with its own JD and checks the right people win.

The paraphrased evidence is deliberately written to share NO salient keyword
with the keyworded evidence, so a pure keyword matcher scores PARAPHRASE_IDEAL
candidates as weak while a semantic engine recognizes them.
"""
from __future__ import annotations

from .datasets import RoleProfile

AI_SEARCH = RoleProfile(
    role_id="ai_search",
    titles_strong=["Senior AI Engineer", "Machine Learning Engineer", "Search Engineer", "Recommendation Systems Engineer"],
    titles_adjacent=["Backend Engineer", "Data Engineer", "Software Engineer", "Platform Engineer"],
    titles_irrelevant=["Marketing Manager", "HR Manager", "Civil Engineer", "Accountant"],
    evidence_keyworded=[
        "Built embeddings-based retrieval and a learning-to-rank ranking model deployed to production for candidate search.",
        "Owned the vector search index (FAISS) and ran NDCG and A/B test evaluation on the ranking pipeline.",
        "Shipped a recommendation system with hybrid retrieval and semantic search at scale.",
    ],
    evidence_paraphrased=[
        "Designed the system that decides which profiles surface first when a recruiter looks for people, and measured whether the ordering improved hiring outcomes.",
        "Stood up the nearest-neighbour lookup over learned profile representations and tuned how results are ordered, comparing variants with live experiments.",
        "Made the 'people you should talk to' suggestions on our platform better by reworking how matches are found and sorted, then proved the lift with offline and online tests.",
    ],
    adjacent_evidence=[
        "Built batch data pipelines on Spark and Airflow feeding analytics dashboards; some exposure to ML feature pipelines.",
        "Backend services in Python with some work on a search feature using Elasticsearch.",
    ],
    weak_evidence=[
        "Wrote CRUD APIs and maintained a Java monolith; took an online course on machine learning.",
    ],
    irrelevant_evidence=[
        "Managed marketing campaigns and email funnels; tracked engagement metrics in spreadsheets.",
    ],
    skills_strong=["Python", "PyTorch", "FAISS", "Embeddings", "Information Retrieval", "Learning to Rank"],
    skills_adjacent=["Python", "Spark", "SQL", "Airflow", "Distributed Systems"],
    locations=["Noida, Uttar Pradesh", "Pune, Maharashtra", "Bangalore, Karnataka", "Hyderabad, Telangana"],
    industry="Software",
)

SALES = RoleProfile(
    role_id="sales",
    titles_strong=["Enterprise Account Executive", "Senior Account Executive", "Regional Sales Manager"],
    titles_adjacent=["Sales Development Rep", "Business Development Manager", "Account Manager"],
    titles_irrelevant=["Software Engineer", "Data Scientist", "Mechanical Engineer"],
    evidence_keyworded=[
        "Carried an enterprise SaaS quota of $2M ARR, owned pipeline generation and closed six-figure deals with strict CRM discipline.",
        "Led the enterprise sales motion for a B2B technology buyer, exceeding quota three years running.",
    ],
    evidence_paraphrased=[
        "Personally responsible for bringing in roughly two million dollars of new yearly revenue from large companies, from first conversation to signed contract, keeping every opportunity meticulously logged.",
        "Drove how we win big-company customers for our business software, beating my targets every year.",
    ],
    adjacent_evidence=[
        "Generated leads and booked meetings for the sales team; some closing experience on small deals.",
        "Managed existing accounts and renewals for mid-market customers.",
    ],
    weak_evidence=["Worked a retail counter and handled walk-in customer queries."],
    irrelevant_evidence=["Wrote backend microservices in Go and managed Kubernetes clusters."],
    skills_strong=["Enterprise Sales", "Pipeline Generation", "Salesforce", "Negotiation", "Forecasting"],
    skills_adjacent=["CRM", "Prospecting", "Account Management"],
    locations=["Mumbai, Maharashtra", "Bangalore, Karnataka", "Delhi"],
    industry="SaaS",
)

DATA_ANALYTICS = RoleProfile(
    role_id="data_analytics",
    titles_strong=["Analytics Lead", "Senior Data Analyst", "Decision Scientist"],
    titles_adjacent=["Business Analyst", "BI Developer", "Data Engineer"],
    titles_irrelevant=["Sales Executive", "Graphic Designer", "Civil Engineer"],
    evidence_keyworded=[
        "Defined company metrics, ran A/B experiments, and built SQL dashboards that drove product decisions with measurable business impact.",
        "Owned experimentation and metric definitions; partnered with product on roadmap decisions backed by data.",
    ],
    evidence_paraphrased=[
        "Decided how the business measures success, set up controlled trials to tell what actually moves the needle, and turned the numbers into choices leadership acted on.",
        "Was the person who figured out what to count and why, and used careful comparisons to settle which product bets were worth making.",
    ],
    adjacent_evidence=[
        "Built dashboards in Tableau from a data warehouse; some experiment analysis.",
        "Wrote SQL reports for stakeholders on a regular cadence.",
    ],
    weak_evidence=["Maintained spreadsheets and pivot tables for monthly reporting."],
    irrelevant_evidence=["Designed marketing creatives and managed social media."],
    skills_strong=["SQL", "Experimentation", "Statistics", "Metrics Design", "Python"],
    skills_adjacent=["Tableau", "Excel", "Reporting"],
    locations=["Bangalore, Karnataka", "Gurgaon, Haryana", "Pune, Maharashtra"],
    industry="Software",
)

BACKEND = RoleProfile(
    role_id="backend",
    titles_strong=["Senior Backend Engineer", "Staff Software Engineer", "Platform Engineer"],
    titles_adjacent=["Software Engineer", "Full Stack Developer", "DevOps Engineer"],
    titles_irrelevant=["Marketing Manager", "Data Analyst", "Sales Executive"],
    evidence_keyworded=[
        "Designed distributed systems and high-throughput APIs on a microservices platform, owned reliability and on-call for production services at scale.",
        "Built and operated databases and message queues handling millions of requests with strong SLAs.",
    ],
    evidence_paraphrased=[
        "Architected the network of services that keep the product running under heavy load, and was the person paged when anything broke, keeping it dependable.",
        "Ran the storage and messaging backbone that absorbs huge traffic without falling over.",
    ],
    adjacent_evidence=[
        "Wrote application features in Python and some service integration work.",
        "Frontend-heavy full stack with occasional backend tickets.",
    ],
    weak_evidence=["Built small scripts and maintained a WordPress site."],
    irrelevant_evidence=["Ran paid ad campaigns and reported on conversions."],
    skills_strong=["Distributed Systems", "Go", "PostgreSQL", "Kafka", "Kubernetes", "System Design"],
    skills_adjacent=["Python", "REST APIs", "Docker"],
    locations=["Bangalore, Karnataka", "Hyderabad, Telangana", "Pune, Maharashtra"],
    industry="Software",
)

PRODUCT = RoleProfile(
    role_id="product",
    titles_strong=["Senior Product Manager", "Group Product Manager", "Principal PM"],
    titles_adjacent=["Associate Product Manager", "Product Owner", "Program Manager"],
    titles_irrelevant=["Backend Engineer", "Accountant", "Sales Executive"],
    evidence_keyworded=[
        "Led product discovery and launched features that moved core metrics; owned the roadmap and drove cross-functional delivery with measurable outcomes.",
        "Shipped customer-facing products end to end, from insight to launch, with clear business results.",
    ],
    evidence_paraphrased=[
        "Figured out what customers actually needed, got the team aligned, and brought new capabilities to market that visibly improved the numbers we cared about.",
        "Took ideas all the way to live products people use, owning the plan and rallying engineering, design and go-to-market.",
    ],
    adjacent_evidence=[
        "Coordinated delivery timelines and wrote tickets; some customer research.",
        "Owned a small feature area under a senior PM.",
    ],
    weak_evidence=["Took meeting notes and tracked tasks for the product team."],
    irrelevant_evidence=["Wrote SQL ETL jobs and maintained data pipelines."],
    skills_strong=["Product Strategy", "Discovery", "Roadmapping", "Metrics", "Stakeholder Management"],
    skills_adjacent=["Agile", "User Research", "Analytics"],
    locations=["Bangalore, Karnataka", "Gurgaon, Haryana", "Mumbai, Maharashtra"],
    industry="Software",
)

DESIGN = RoleProfile(
    role_id="design",
    titles_strong=["Senior Product Designer", "Staff Designer", "Design Systems Lead"],
    titles_adjacent=["UX Designer", "UI Designer", "Interaction Designer"],
    titles_irrelevant=["Backend Engineer", "Sales Executive", "Accountant"],
    evidence_keyworded=[
        "Shipped end-to-end product design with a design system, ran user research and usability testing, and validated interaction design with real users.",
        "Owned the design system and shipped usable, validated interfaces across the product.",
    ],
    evidence_paraphrased=[
        "Built and maintained the shared kit of components the whole product is made from, watched real people use what I made, and reworked it until it actually worked for them.",
        "Took screens from idea to shipped, proving with real users that the experience held up.",
    ],
    adjacent_evidence=[
        "Designed UI mockups in Figma; some user testing.",
        "Visual design and marketing assets with occasional product screens.",
    ],
    weak_evidence=["Made slide templates and edited images."],
    irrelevant_evidence=["Wrote backend APIs and database migrations."],
    skills_strong=["Product Design", "Design Systems", "User Research", "Figma", "Interaction Design"],
    skills_adjacent=["UI Design", "Prototyping", "Usability Testing"],
    locations=["Bangalore, Karnataka", "Pune, Maharashtra", "Remote"],
    industry="Software",
)

ROLES = {
    r.role_id: r
    for r in [AI_SEARCH, SALES, DATA_ANALYTICS, BACKEND, PRODUCT, DESIGN]
}
