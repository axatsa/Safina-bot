FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Make entrypoint script executable and ensure LF line endings
RUN apt-get update && apt-get install -y sed && \
    sed -i 's/\r$//' scripts/entrypoint.sh && \
    chmod +x scripts/entrypoint.sh

# Run the application
ENTRYPOINT ["/bin/bash", "/app/scripts/entrypoint.sh"]
