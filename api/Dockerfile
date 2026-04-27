FROM python:3.12-slim-bullseye

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements-prod.txt

COPY src/ src/

ENV LOGICAL_DB_PATH=/data/logical_release.db
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn","src.api.app:app","--host","0.0.0.0","--port","8000"]
