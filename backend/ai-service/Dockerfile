# Use a slim, modern Python base
FROM python:3.11-slim

# Avoid writing .pyc and get unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# System deps (if you hit build errors for numpy/scipy/shap, uncomment below)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#  && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Build-time training — bakes models into the image
RUN python train.py

# Expose the API port
EXPOSE 5004

# Set environment variables for gunicorn
ENV GUNICORN_BIND=0.0.0.0:5004
ENV PORT=5004

# Use Uvicorn with multiple workers
# --workers 2: 2 worker processes (scale based on CPU cores)
# --timeout-keep-alive 300: 5 min timeout (to allow rebuilds)
# --host 0.0.0.0 --port 5004: bind to container port 5004
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5004", "--workers", "2", "--timeout-keep-alive", "300"]
