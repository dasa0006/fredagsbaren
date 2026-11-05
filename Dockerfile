FROM python:3.12-slim

# Hent uv fra det officielle image, så afhængighederne installeres præcis som lokalt.
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installér afhængigheder først, så Docker-cachen kan genbruges.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api.py app.py swagger.json ./

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000 8501

# Overskrives af docker-compose.yml, så begge services kan bruge samme image.
CMD ["python", "api.py"]
