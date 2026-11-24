FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN uv venv /opt/venv

COPY requirements.txt .
RUN uv pip install --python /opt/venv/bin/python -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]
