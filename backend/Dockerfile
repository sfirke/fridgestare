FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml /app/pyproject.toml
# The package itself is installed from the source copied below; this layer exists
# only so dependency installation is cached separately from application changes.
RUN mkdir -p /app/app && touch /app/app/__init__.py \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .[dev]

COPY backend /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
