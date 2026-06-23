"""Realistic messy resume fixtures (synthetic, no real PII) — the inputs a real
product actually receives. Each tests a different parsing challenge the local
free-text parser must handle. Used to harden ingest.resume_parser.
"""

# 1. Paragraph-style (no section headers, no date lines) — the case that broke today
PARAGRAPH = """Arjun Nair, based in Bangalore. A staff AI engineer with about 8 years of
experience. Built a production AI agent platform and RAG systems, did MCP integrations
and multi-LLM routing. Strong in Python and TypeScript, REST and GraphQL. Shipped LLM
products to real users and led a small team. Skilled in AI Agents, RAG, MCP, LLMs,
Guardrails."""

# 2. Bullets with dates but no "Title at Company" pattern
BULLETS_DATES = """Maria Schmidt
Berlin, Germany

EXPERIENCE
Senior AI Engineer, Acme AI (2019 - Present)
- Shipped production LLM agents with prompt engineering and tool-calling
- Built guardrails and evaluation across OpenAI and Anthropic models
ML Engineer, DataCorp (2016 - 2019)
- Built recommendation models

SKILLS: Python, TypeScript, LLMs, Prompt Engineering, AI Agents, GraphQL
"""

# 3. Dates on a separate line from the title (common real layout)
SPLIT_DATES = """Ravi Menon
Bengaluru, India

Staff Software Engineer
IBM
Feb 2019 - Present
Built a multi-LLM conversational platform, RAG assistants and MCP servers.
Created an open-source LLM SDK with 40K downloads.

Senior Engineer
Poornam
2011 - 2018
Led cloud management product development.

SKILLS
Python, TypeScript, LLMs, RAG, AI Agents, MCP, GraphQL, Kubernetes
"""

# 4. Terse / undersell (great person, minimal words)
TERSE = """Sana Iyer. Pune. AI engineer, 6 years. Did LLM agents and chatbots. Python."""

# 5. ALL CAPS headers, pipe-separated skills, unusual spacing
CAPS_PIPES = """TOM BECKER  |  LONDON, UK

WORK HISTORY
BACKEND ENGINEER | TECHCO | 2018-PRESENT
Java and Python microservices, REST APIs. Added an LLM feature using OpenAI.

TECHNICAL SKILLS
Java | Python | REST | OpenAI | Docker
"""

# 6. Keyword-stuffer (claims everything in skills, career says marketing)
STUFFER = """Vikram Reddy
Hyderabad, India

EXPERIENCE
Marketing Manager, BrandAgency, 2015 - Present
Ran marketing campaigns and email funnels. Tracked engagement in spreadsheets.

SKILLS
Python, LLMs, AI Agents, Prompt Engineering, GraphQL, RAG, MCP, Guardrails, Kubernetes, Embeddings
"""

# Expected (rough) ground truth for assertions — what a good parse should recover.
EXPECTED = {
    "PARAGRAPH":   {"min_years": 7, "max_years": 9, "has_title": True, "min_skills": 3, "min_career": 1},
    "BULLETS_DATES": {"min_years": 5, "max_years": 12, "has_title": True, "min_skills": 3, "min_career": 2},
    "SPLIT_DATES": {"min_years": 5, "max_years": 16, "has_title": True, "min_skills": 4, "min_career": 2},
    "TERSE":       {"min_years": 5, "max_years": 7, "has_title": True, "min_skills": 1, "min_career": 0},
    "CAPS_PIPES":  {"min_years": 5, "max_years": 12, "has_title": True, "min_skills": 3, "min_career": 1},
    "STUFFER":     {"min_years": 8, "max_years": 12, "has_title": True, "min_skills": 5, "min_career": 1},
}

ALL = {
    "PARAGRAPH": PARAGRAPH, "BULLETS_DATES": BULLETS_DATES, "SPLIT_DATES": SPLIT_DATES,
    "TERSE": TERSE, "CAPS_PIPES": CAPS_PIPES, "STUFFER": STUFFER,
}
