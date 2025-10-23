# Dockerfile for SEC filing data processing pipeline
# Handles chunking, embedding generation, and RAPTOR processing

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching optimization)
COPY ../requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app/src/

# Set Python to unbuffered mode (see output in real-time)
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "src.data.text_processor", "--help"]
