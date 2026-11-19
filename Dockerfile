FROM python:3.14-slim
LABEL org.opencontainers.image.source="https://github.com/Tedyst/HikLoad"

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    RUNNING_IN_DOCKER=TRUE

COPY pyproject.toml uv.lock README.md /app/
RUN uv sync --locked --no-dev --no-install-project

COPY main.py /app/
COPY hikload /app/hikload
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["hikload"]
