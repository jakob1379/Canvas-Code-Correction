# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.13-slim-bookworm
FROM python:${PYTHON_VERSION} AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --no-managed-python --frozen

FROM python:${PYTHON_VERSION} AS runner

ARG APP_UID=1001
ARG APP_GID=1001
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN addgroup --system --gid ${APP_GID} app && \
    adduser \
      --system \
      --uid ${APP_UID} \
      --gid ${APP_GID} \
      --home /app \
      --shell /bin/bash \
      app

COPY --from=base /app/.venv ./.venv
COPY . /app

RUN chown -R ${APP_UID}:${APP_GID} /app

USER app

ENV PATH="/app/.venv/bin:${PATH}"

ENTRYPOINT ["python", "-m", "canvas_code_correction.runner"]
