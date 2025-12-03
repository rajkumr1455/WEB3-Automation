FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Foundry
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /root/.foundry/bin/foundryup

ENV PATH="/root/.foundry/bin:${PATH}"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Echidna (optional, can be added later)
# RUN wget https://github.com/crytic/echidna/releases/download/v2.2.1/echidna-2.2.1-Linux.tar.gz && \
#     tar -xzf echidna-2.2.1-Linux.tar.gz && \
#     mv echidna /usr/local/bin/

# Copy application code
COPY app.py .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8004

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8004"]
