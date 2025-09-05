FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential netcat-traditional && rm -rf /var/lib/apt/lists/*
RUN useradd -m appuser

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=appuser:appuser backend/ /app

COPY --chown=appuser:appuser backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown appuser:appuser /entrypoint.sh

USER appuser

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
