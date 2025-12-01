FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Create data directories
RUN mkdir -p data/db data/uploads

# Expose port
EXPOSE 8000

# Start server - use PORT env var for Railway
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
