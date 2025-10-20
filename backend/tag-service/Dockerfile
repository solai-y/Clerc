FROM python:3.11-slim

WORKDIR /app

# Install any required OS dependencies
RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 5007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5007/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5007"]
