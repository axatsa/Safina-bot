#!/bin/bash
# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
    echo "❌ Migration failed! Aborting startup."
    exit 1
fi

# Start the application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
