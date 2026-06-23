# Reproduction image for the RANKING STEP only.
#
# The ranking step is CPU-only, offline, and within 5 min / 16 GB. The spine
# engine needs no dependencies; the hybrid engine needs only numpy (to load the
# precomputed index). sentence-transformers/torch are NOT installed here — they
# are precompute-only. Offline env vars guarantee no code path reaches the
# network even if a heavy import were attempted.
FROM python:3.11-slim

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    TOKENIZERS_PARALLELISM=false \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install only the rank-time dependency (numpy). Network is available at BUILD
# time; the reproduction RUN can be executed with --network none.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Default: spine engine (zero-dependency, always reproduces).
# For the hybrid engine, run with: --engine hybrid --index-dir outputs/index
CMD ["python", "rank.py", \
     "--candidates", "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl", \
     "--out", "outputs/final_submission.csv"]
