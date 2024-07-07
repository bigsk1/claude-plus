#!/bin/bash
# docker/start-dev.sh

# Start the backend
uvicorn backend:app --reload --host 0.0.0.0 --port 8000 &

# Change to frontend directory
cd /app/frontend

# Start the frontend
npm run dev -- --host 0.0.0.0