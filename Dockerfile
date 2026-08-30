FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /app/.venv .venv
COPY huerise/ ./huerise/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "huerise.main:app", "--host", "0.0.0.0", "--port", "8000"]
