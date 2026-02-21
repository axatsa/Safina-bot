# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Set PYTHONPATH to current directory so 'bot' and other modules are found
ENV PYTHONPATH=/app

# Command to run both API and Bot (using a simple script or separate containers)
# For simplicity in one container, we can use a small script, but docker-compose is better for separate services.
# I will set the default command to run the API, but we'll override it in docker-compose.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
