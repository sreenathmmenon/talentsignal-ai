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

# IMPORTANT: the committed outputs/final_submission.csv is the HYBRID engine's
# output. Build this image from a checkout that has pulled Git-LFS objects
# (`git lfs install && git lfs pull`) so outputs/index/*.npy are the real files,
# not pointers — otherwise the hybrid step aborts with an actionable message.
#
# Default: reproduce the SUBMITTED (hybrid) CSV to a SEPARATE path, leaving the
# committed submission untouched. Compare the two to confirm reproduction:
#   docker run --network none --rm talentsignal-ai \
#     && diff outputs/repro_submission.csv outputs/final_submission.csv
CMD ["python", "rank.py", \
     "--engine", "hybrid", "--index-dir", "outputs/index", \
     "--candidates", "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl", \
     "--out", "outputs/repro_submission.csv"]
