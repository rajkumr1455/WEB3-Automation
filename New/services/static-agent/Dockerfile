FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Solidity compiler
RUN curl -L https://github.com/ethereum/solidity/releases/download/v0.8.23/solc-static-linux -o /usr/local/bin/solc && \
    chmod +x /usr/local/bin/solc

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8003

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
