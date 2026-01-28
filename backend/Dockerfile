# backend/Dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Retry-friendly apt-get (helps flaky networks)
RUN set -eux; \
    retries=5; \
    count=0; \
    until [ $count -ge $retries ]; do \
      apt-get update && break || { count=$((count+1)); echo "apt-get update failed, retry #${count}"; sleep 3; }; \
    done; \
    apt-get install -y --no-install-recommends \
      build-essential libpq-dev libjpeg-dev zlib1g-dev libffi-dev wget curl git ca-certificates \
    || (apt-get update && apt-get install -y --no-install-recommends \
      build-essential libpq-dev libjpeg-dev zlib1g-dev libffi-dev wget curl git ca-certificates); \
    rm -rf /var/lib/apt/lists/*

# Copy python requirements and install
COPY requirements.txt /code/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /code/requirements.txt

# Copy backend source (make sure your entrypoint.sh exists and is executable)
COPY . /code
RUN chmod +x /code/entrypoint.sh || true

EXPOSE 8000

CMD ["./entrypoint.sh"]
