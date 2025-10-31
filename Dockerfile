FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy backend, frontend, and requirements
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI server (correct import path)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
