FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python modules
COPY *.py .

# Copy worker entrypoint script
COPY worker_entrypoint.sh /app/
RUN chmod +x /app/worker_entrypoint.sh

# Create data directories
RUN mkdir -p /app/scans /app/reports

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
