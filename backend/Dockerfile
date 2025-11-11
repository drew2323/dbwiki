# Multi-stage build for Python FastAPI backend

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy Python dependencies from builder to appuser's home
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Create startup script
COPY --chown=appuser:appuser <<'EOF' /app/start.sh
#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until python -c "from app.database import get_engine; get_engine().connect()" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - running migrations"
alembic upgrade head

echo "Starting application"
exec uvicorn main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]
