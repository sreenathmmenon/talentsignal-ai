FROM python:3.11-slim

WORKDIR /app
COPY . /app

CMD ["python", "rank.py", "--candidates", "[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl", "--out", "outputs/final_submission.csv"]

