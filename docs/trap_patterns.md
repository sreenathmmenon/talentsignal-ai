# Trap Patterns And Risk Rules

## Purpose

The dataset includes keyword stuffers and honeypot-like candidates. The ranker should avoid them naturally by requiring career evidence and consistency.

## Trap Patterns

### AI Keyword Stuffing

Signals:

- Many AI skills listed.
- Weak or unrelated current title.
- No career-history descriptions involving ML/search/retrieval/ranking systems.
- Low skill duration or low endorsements.

Action:

- Penalize skill-only AI evidence.
- Require career evidence for top-10 eligibility.

### Non-Tech Candidate With AI Skills

Signals:

- Current title is HR Manager, Marketing Manager, Sales Executive, Accountant, Operations Manager, Customer Support, Graphic Designer, Content Writer, Civil/Mechanical Engineer.
- Skills include AI terms but career text does not support AI engineering work.

Action:

- Strong title/career mismatch penalty.

### Pure Research Without Deployment

Signals:

- Research terms dominate.
- No deployed, production, user-facing, shipped, A/B, scale, latency, or evaluation terms.

Action:

- Penalize for Redrob JD unless production evidence exists.

### Shallow AI Tool Usage

Signals:

- Mentions ChatGPT, AI tools, curiosity, productivity, or experiments without production ML systems.

Action:

- Treat as weak interest signal, not role fit.

### Stale Or Unavailable Candidate

Signals:

- Old last active date.
- Low recruiter response rate.
- Very slow response time.
- Not open to work.
- Long notice period.

Action:

- Down-rank unless technical evidence is exceptional.

### Service-Only Career

Signals:

- Career path only in known IT services/consulting companies.
- No product-company evidence.

Action:

- Penalize moderately to strongly, depending on technical evidence.

### Impossible Or Suspicious Skills

Signals:

- Multiple expert skills with zero duration.
- Many unrelated advanced/expert skills with no assessment or career support.

Action:

- Add suspicious profile risk flag and penalty.

