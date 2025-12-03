# Test Docker Environment
FROM python:3.11-slim

WORKDIR /app

# Install test dependencies
COPY tests/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY tests/ /app/tests/

# Set environment variables
ENV PYTHONPATH=/app

CMD ["python", "-m", "pytest", "tests/backend", "-v", "--tb=short"]
