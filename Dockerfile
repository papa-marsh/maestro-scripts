FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py ./
COPY scripts/ ./scripts
COPY custom_domains/ ./custom_domains
COPY registry/ ./registry

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
