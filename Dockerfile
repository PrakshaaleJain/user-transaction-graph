FROM python:3.11-slim

WORKDIR /app

# Copy backend source and requirements
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Uvicorn
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
