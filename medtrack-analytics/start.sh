#!/bin/bash

# Start the database
echo "Starting PostgreSQL database..."
docker-compose up -d

# Wait for database to be ready
sleep 5

# Activate virtual environment if present
if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt

# Run the application
echo "Starting MedTrack Analytics API..."
python run.py
