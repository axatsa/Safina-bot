#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY=0
until python3 -c "
import os, sys
from sqlalchemy import create_engine, text
try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('Database is ready!')
    sys.exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo "❌ Database not ready after $MAX_RETRIES attempts. Aborting."
        exit 1
    fi
    echo "  Attempt $RETRY/$MAX_RETRIES..."
    sleep 2
done

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head
if [ $? -ne 0 ]; then
    echo "❌ Migration failed! Aborting startup."
    exit 1
fi
echo "✅ Migrations applied successfully."

# Start the application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
