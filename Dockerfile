# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry==1.4.2

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy source code
COPY sqlproxy sqlproxy/

# Production stage
FROM python:3.9-slim

WORKDIR /app

# Copy dependencies and source from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app/sqlproxy /app/sqlproxy

# Runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 sqlproxy
USER sqlproxy

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "from sqlproxy.core.health import check_health; check_health()"

# Start command
CMD ["python", "-m", "sqlproxy"]