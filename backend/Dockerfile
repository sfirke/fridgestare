# Two targets share one dependency layer: `dev` keeps the test and lint extras that
# Compose and CI want, `runtime` ships only what the server needs and runs unprivileged.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml /app/pyproject.toml
# The package itself is installed from the source copied below; this layer exists
# only so dependency installation is cached separately from application changes.
RUN mkdir -p /app/app && touch /app/app/__init__.py \
    && pip install --no-cache-dir --upgrade pip


FROM base AS dev

RUN pip install --no-cache-dir -e .[dev]
COPY backend /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM base AS runtime

RUN pip install --no-cache-dir -e .
COPY backend /app

# The scheduler and the rate-limit log both live in process memory, so this image is
# meant to run as a single worker. Scaling out needs a shared store for both first.
RUN useradd --create-home --uid 10001 fridgestare && chown -R fridgestare:fridgestare /app
USER fridgestare

# --proxy-headers with the reverse proxy's address in --forwarded-allow-ips is what
# makes request.client the real caller rather than the proxy, which the login rate
# limiter buckets on. Compose passes the concrete allow-list.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
