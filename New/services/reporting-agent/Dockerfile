FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Copy templates
COPY templates/ /app/templates/

# Create reports directory
RUN mkdir -p /app/reports

# Expose port
EXPOSE 8007

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8007"]
