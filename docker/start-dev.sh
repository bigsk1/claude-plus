#!/bin/bash
# docker/start-dev.sh

# Start the backend - Can use uvicorn backend:app --reload --host 0.0.0.0 --port 8000  but it will forget what it was doing on reload
# Currently automode iteration updates not showing with reload off - still troubleshooting, usinbg reload they will show an update after each iteration 
uvicorn backend:app --host 0.0.0.0 --port 8000 &

# Change to frontend directory
cd /app/frontend

# Start the frontend
npm run dev -- --host 0.0.0.0