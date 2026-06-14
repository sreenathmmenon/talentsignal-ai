# First Prize Premortem

This document assumes we failed to win first prize and asks why. The purpose is to expose risks early, reduce blind spots, and turn failure modes into engineering tasks.

## Top-Level Failure Thesis

We can lose even with a working submission if:

- The top 10 is weaker than competitors.
- The system over-ranks keyword stuffers.
- The hidden ground truth rewards signals we underweight.
- The CSV or code fails reproduction.
- The reasoning fails manual review.
- The product/demo does not impress.
- We cannot defend the architecture in interview.

## Premortem Failure Points

### Ranking Quality Failures

1. Top 10 contains candidates with AI keywords but no real production AI experience.
2. Top 10 contains non-technical candidates due to skill-list keyword stuffing.
3. Top 10 misses actual search/retrieval/recommendation engineers hidden in plain language.
4. Top 10 overweights current title and misses strong career-history evidence.
5. Top 10 underweights current title and includes irrelevant career paths.
6. Top 10 overweights skills and underweights career descriptions.
7. Top 10 overweights TF-IDF similarity and repeats the keyword-matching trap.
8. Top 10 underweights product-company experience.
9. Top 10 underweights production deployment evidence.
10. Top 10 includes pure research candidates that JD explicitly warns against.
11. Top 10 includes CV/speech/robotics-heavy candidates without NLP/IR relevance.
12. Top 10 includes candidates with too little experience for senior role.
13. Top 10 includes candidates with too much experience and likely title/role mismatch.
14. Top 10 includes stale profiles with low likelihood of hiring success.
15. Top 10 includes candidates outside India without relocation evidence.
16. Top 10 includes candidates with long notice periods where stronger alternatives exist.
17. Top 10 ignores recruiter response rate.
18. Top 10 ignores recent activity.
19. Top 10 ignores verification and profile completeness.
20. Top 10 ignores interview completion and offer acceptance.
21. Top 10 over-penalizes non-perfect logistics and misses technically excellent candidates.
22. Top 10 over-penalizes service-company experience even when candidate has product evidence.
23. Top 10 under-penalizes service-only career paths.
24. Top 10 includes candidates whose summaries are aspirational, not evidence-based.
25. Top 10 lacks enough direct ranking/retrieval/search evidence.
26. Top 50 is too narrow and misses relevant adjacent candidates.
27. Top 100 includes many filler candidates that hurt MAP.
28. Ranking score is not calibrated enough to separate close candidates.
29. Tie-breaking accidentally changes candidate order in a harmful way.
30. Manual audit fixes one obvious issue but introduces another.

### JD Understanding Failures

31. We treat the JD as a list of skills instead of a hiring narrative.
32. We miss the founding-team/product-engineering emphasis.
33. We miss the "shipper over researcher" preference.
34. We miss the requirement for ranking evaluation experience.
35. We miss the importance of hybrid search/vector infrastructure.
36. We miss the warning against shallow LangChain/API-only experience.
37. We miss the concern about people who stopped writing code.
38. We miss location nuance: Pune/Noida preferred but broader India acceptable.
39. We treat 5-9 years as a hard filter and exclude strong outliers.
40. We treat 5-9 years as irrelevant and include weak seniority fits.
41. We miss culture signals around writing, async work, and fast decisions.
42. We fail to map career-history plain language to JD intent.
43. We fail to separate must-have from nice-to-have signals.
44. We fail to understand that hidden relevance tiers likely encode JD caveats.
45. We optimize for generic AI engineer instead of Redrob's specific need.

### Feature Engineering Failures

46. Text normalization loses important signals such as "A/B", "NDCG", or ".NET".
47. Skill aliases are incomplete, so relevant candidates are missed.
48. Retrieval synonyms are incomplete, missing search/recommender candidates.
49. Vector database aliases are incomplete.
50. Production evidence phrases are too narrow.
51. Product-company detection is weak.
52. Service-company detection is too aggressive.
53. Location parsing is too crude.
54. Experience scoring has bad thresholds.
55. Behavioral features are not normalized properly.
56. Missing values are handled incorrectly.
57. Negative sentinel values like `-1` offer acceptance or GitHub score are misread.
58. Skill duration is ignored.
59. Skill endorsements are overtrusted.
60. Skill proficiency is overtrusted.
61. Assessment scores are ignored.
62. Career-history descriptions are underused.
63. Current company/industry are overused.
64. Education is overweighted despite JD emphasizing production experience.
65. Certifications are overweighted.
66. Open-source/external validation signals are missed.
67. Job-hopping risk is ignored.
68. Tenure and career progression are ignored.
69. Candidate availability signals are combined linearly when they should gate risky candidates.
70. Suspicious profile detection is too shallow.

### Trap And Honeypot Failures

71. Honeypot profiles enter top 100.
72. More than 10 percent of top 100 are honeypots, causing disqualification.
73. Expert skills with zero duration are not detected.
74. Impossible company/date combinations are not detected.
75. Excessive unrelated expert skills are not detected.
76. Skill stuffing beats career evidence.
77. Non-tech profiles with AI skills are ranked too high.
78. Generic AI curiosity language is mistaken for production experience.
79. Candidate summaries contradict career history and we miss it.
80. Current title contradicts career descriptions and we miss it.
81. Location/relocation contradictions are missed.
82. Salary/logistics outliers are ignored.
83. Inactive candidates are ranked high because static fit is strong.
84. Low response candidates are ranked high because static fit is strong.
85. Profiles with no assessments are treated the same as profiles with strong assessments.
86. Candidate IDs in sample submission bias our thinking.
87. We overfit to visible sample candidates.
88. We assume all synthetic data patterns are meaningful when some may be noise.
89. We create brittle hand-coded honeypot rules that accidentally remove good candidates.
90. We fail to manually inspect suspicious high-scoring candidates.

### Explainability Failures

91. Reasoning mentions skills not present in the candidate profile.
92. Reasoning mentions employers not present in career history.
93. Reasoning claims production experience without evidence.
94. Reasoning is generic and templated.
95. Reasoning does not connect to the JD.
96. Reasoning is too short to be useful.
97. Reasoning is too long and gets hard to review.
98. Reasoning tone does not match rank.
99. Top-ranked candidates have cautious explanations that undermine confidence.
100. Low-ranked candidates have glowing explanations that look inconsistent.
101. Reasoning fails to acknowledge obvious concerns.
102. Reasoning repeats the same phrase across many rows.
103. Reasoning uses jargon to sound impressive but lacks facts.
104. Reasoning includes unverified inferences.
105. Manual review samples weak rows and penalizes us.

### Reproducibility And Constraint Failures

106. Final command exceeds 5 minutes.
107. Final command exceeds 16 GB RAM.
108. Final command requires network access.
109. Final command depends on a hosted API.
110. Final command depends on GPU.
111. Final command depends on files not included in repo or documented.
112. Final command depends on local absolute paths.
113. Final command fails in Linux even if it works on Mac.
114. Requirements are incomplete.
115. Dependency versions are not pinned enough.
116. A package install fails in reviewer environment.
117. Code reads the wrong input path.
118. Code writes the wrong output filename.
119. Randomness makes rankings non-deterministic.
120. Precomputed artifacts are missing or too large.
121. README reproduction command is wrong.
122. Code requires manual steps not documented.
123. Validator passes locally but not in clean environment due to encoding/newline issue.
124. CSV has malformed quoting in reasoning.
125. Candidate IDs do not all exist in the dataset.

### Submission Format Failures

126. CSV has 99 or 101 rows.
127. Header order is wrong.
128. Rank starts at 0.
129. Duplicate ranks exist.
130. Duplicate candidate IDs exist.
131. Scores increase at some rank.
132. Equal-score tie-break is not deterministic.
133. File extension or filename is wrong.
134. File encoding is not UTF-8.
135. Reasoning contains commas or quotes that are not escaped correctly.
136. Final uploaded file is not the validated file.
137. Metadata is incomplete.
138. GitHub repo URL is wrong or inaccessible.
139. Sandbox/demo link is broken.
140. AI tools declaration is incomplete or inconsistent.

### Methodology And Review Failures

141. Methodology sounds like generic AI text.
142. Methodology does not explain why keyword matching fails.
143. Methodology does not explain hidden trap handling.
144. Methodology does not explain behavioral signals.
145. Methodology does not explain scoring tradeoffs.
146. Methodology overclaims model sophistication.
147. Methodology underclaims product thinking.
148. Methodology does not match submitted code.
149. Methodology is too long and unfocused.
150. Methodology lacks runtime and reproducibility details.
151. Reviewers cannot tell what is original engineering.
152. Git history is flat and looks like a last-minute dump.
153. Code quality looks rushed.
154. Important constants are unexplained.
155. There are no tests.

### Product And Demo Failures

156. Demo is broken at review time.
157. Demo is slow.
158. Demo does not accept a sample JD or candidates.
159. Demo does not show score breakdown.
160. Demo does not show risk flags.
161. Demo looks like a notebook, not a product.
162. Demo UI distracts from ranking quality.
163. Demo overpromises generality that code does not support.
164. Demo cannot export CSV.
165. Demo uses live APIs in a way that confuses final reproducibility.
166. Demo lacks a clear product story.
167. Demo does not show why our system is better than keyword search.
168. Demo has visual polish but weak substance.
169. Demo has substance but is hard to understand quickly.
170. Demo cannot be run by judges.

### Interview Defense Failures

171. We cannot explain the scoring rubric clearly.
172. We cannot explain why top candidate is ranked first.
173. We cannot explain why a visible AI-keyword candidate was down-ranked.
174. We cannot explain how behavioral signals are used.
175. We cannot explain compute tradeoffs.
176. We cannot explain why we did not use a large LLM in final ranking.
177. We cannot explain how the system generalizes to other JDs.
178. We cannot explain failure modes honestly.
179. We contradict the code during interview.
180. We overclaim benchmark performance without evidence.
181. We cannot defend manual audit choices.
182. We cannot explain hidden scoring metrics like NDCG and MAP.
183. We cannot explain how hallucinations are prevented.
184. We cannot explain how honeypots are avoided.
185. We sound like the system was mostly generated without understanding.

### Competitive Failures

186. Competitors use stronger manual audit and better top-10 precision.
187. Competitors discover more dataset-specific trap patterns.
188. Competitors build better candidate evidence extraction.
189. Competitors use stronger semantic embeddings in precomputation while staying reproducible.
190. Competitors tune scoring more carefully.
191. Competitors have better methodology storytelling.
192. Competitors have a more polished demo.
193. Competitors submit earlier and win timestamp tiebreaks.
194. Competitors have better interview defense.
195. Competitors make fewer operational mistakes.

### Project Management Failures

196. We spend too much time planning and not enough time ranking.
197. We spend too much time building UI and not enough time improving top 10.
198. We over-engineer general JD support before winning the reference JD.
199. We change scoring late and do not re-audit top candidates.
200. We do not preserve experiment results.
201. We do not track decisions.
202. We do not make incremental commits.
203. We do not leave time for clean reproduction testing.
204. We submit without a final checklist.
205. We burn submissions before the system is ready.

## Countermeasures

1. Make top-10 precision the primary engineering metric.
2. Build the baseline quickly, then iterate from real outputs.
3. Keep Redrob JD optimization above general product ambition.
4. Manually audit top 25 after every major scoring change.
5. Use structured evidence for every high-rank explanation.
6. Penalize skill stuffing unless supported by career evidence.
7. Add explicit suspicious-profile checks.
8. Use behavioral signals as real hiring likelihood, not decoration.
9. Keep final ranking command simple and deterministic.
10. Validate CSV on every generated submission.
11. Run clean reproduction before submission.
12. Document every major scoring choice.
13. Build a demo only after core ranking quality is credible.
14. Prepare interview defense from the actual code and candidate examples.
15. Do not submit until top candidates are defensible.

## Red-Flag Checklist Before Final Submission

- Any non-tech or irrelevant current title in top 10?
- Any top-10 candidate without production ML/search/ranking evidence?
- Any top-10 candidate stale or very low response?
- Any top-25 candidate whose reasoning mentions unsupported facts?
- Any obvious strong candidate below rank 50?
- Any suspicious skill-stuffing profile in top 100?
- Does official validator pass?
- Does one-command reproduction work?
- Does final command obey CPU/no-network/no-GPU constraints?
- Can we defend rank 1, rank 10, rank 50, and rank 100?

