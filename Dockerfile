FROM python:3.14-slim AS builder

ARG AUDIO_BACKENDS=local

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
RUN case "$AUDIO_BACKENDS" in \
      local|sonos) uv sync --frozen --no-dev --extra "$AUDIO_BACKENDS" ;; \
      all) uv sync --frozen --no-dev --all-extras ;; \
      *) echo "AUDIO_BACKENDS must be local, sonos, or all" >&2; exit 1 ;; \
    esac


FROM python:3.14-slim AS runtime

ARG AUDIO_BACKENDS=local

WORKDIR /app

RUN if [ "$AUDIO_BACKENDS" = local ] || [ "$AUDIO_BACKENDS" = all ]; then \
      apt-get update && apt-get install -y libportaudio2 && \
      rm -rf /var/lib/apt/lists/*; \
    fi

COPY --from=builder /app/.venv .venv
COPY huerise/ ./huerise/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV AUDIO_BACKENDS=$AUDIO_BACKENDS

CMD ["python", "-m", "uvicorn", "huerise.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]


FROM python:3.14-slim AS dev

ARG AUDIO_BACKENDS=local

WORKDIR /app

RUN if [ "$AUDIO_BACKENDS" = local ] || [ "$AUDIO_BACKENDS" = all ]; then \
      apt-get update && apt-get install -y libportaudio2 && \
      rm -rf /var/lib/apt/lists/*; \
    fi

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
RUN case "$AUDIO_BACKENDS" in \
      local|sonos) uv sync --frozen --extra "$AUDIO_BACKENDS" ;; \
      all) uv sync --frozen --all-extras ;; \
      *) echo "AUDIO_BACKENDS must be local, sonos, or all" >&2; exit 1 ;; \
    esac

COPY huerise/ ./huerise/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV AUDIO_BACKENDS=$AUDIO_BACKENDS

CMD ["python", "-m", "uvicorn", "huerise.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--loop", "asyncio"]
