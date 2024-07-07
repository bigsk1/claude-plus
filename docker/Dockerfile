# Base image
FROM node:18 as frontend-builder

# Set working directory
WORKDIR /app/frontend

# Copy package.json and package-lock.json
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend ./

# Build frontend
RUN npm run build

# Backend and final image
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY requirements.txt .

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend.py shared_utils.py ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy the projects folder
COPY projects ./projects

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]