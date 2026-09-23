# Build from the repo root: docker build -f infra/docker/api.Dockerfile .
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so code changes don't bust the layer cache.
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package lanterngrid-api

COPY apps/api/ apps/api/
WORKDIR /app/apps/api

RUN useradd --create-home --uid 1000 app
USER app

EXPOSE 8000
# Run migrations as a pre-deploy step (`alembic upgrade head`), not here, so multiple
# replicas never race each other.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
