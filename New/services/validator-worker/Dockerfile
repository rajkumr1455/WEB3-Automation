# Multi-stage build for Validator Worker

FROM ghcr.io/foundry-rs/foundry:latest AS foundry

FROM python:3.11-slim

WORKDIR /app

# Copy Foundry from foundry image
COPY --from=foundry /usr/local/bin/forge /usr/local/bin/forge
COPY --from=foundry /usr/local/bin/cast /usr/local/bin/cast
COPY --from=foundry /usr/local/bin/anvil /usr/local/bin/anvil

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8010/health')"

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010", "--workers", "1"]
