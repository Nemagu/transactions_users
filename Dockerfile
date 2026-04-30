FROM python:3.14-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

RUN useradd --create-home --home-dir /app --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-dev --no-install-project

COPY src/. ./
COPY yoyo.ini ./yoyo.ini

USER appuser

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "main.py"]
