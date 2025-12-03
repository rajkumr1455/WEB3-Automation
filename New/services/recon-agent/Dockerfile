FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8002

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
