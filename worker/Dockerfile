FROM python:3.12-slim

# System dependencies required for soundfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install only worker dependencies
COPY worker/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# Copy worker runtime source
COPY worker/src/ml_worker /app/ml_worker

ENV PYTHONUNBUFFERED=1

CMD ["python", "ml_worker/worker.py"]


