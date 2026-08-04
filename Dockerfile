FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev


FROM python:3.14-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y libportaudio2 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv .venv
COPY huerise/ ./huerise/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "huerise.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]


FROM python:3.14-slim AS dev

WORKDIR /app

RUN apt-get update && apt-get install -y libportaudio2 && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen

COPY huerise/ ./huerise/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "huerise.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--loop", "asyncio"]
