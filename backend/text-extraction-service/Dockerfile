# Text Extraction Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and health checks
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5008

# Set environment variables
ENV PORT=5008
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5008/health || exit 1

# Run the application
CMD ["python", "app.py"]