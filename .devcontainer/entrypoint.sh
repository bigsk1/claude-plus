#!/bin/bash

# Start the backend
uvicorn backend:app --reload --host 0.0.0.0 --port 8000 &

# Change to frontend directory
cd frontend

# Start the frontend
npm run dev -- --host 0.0.0.0

# Keep the container running
tail -f /dev/null