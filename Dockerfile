# Multi-service Python container for FinTrack
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Generate dataset and train initial ML model artifact inside build
RUN python scripts/generate_dataset.py && python scripts/train_model.py

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Default entrypoint runs FastAPI backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
