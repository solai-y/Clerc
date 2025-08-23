FROM python:3.11-slim
WORKDIR /app

# curl for healthcheck; tesseract for OCR fallback
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/app.py
COPY wsgi.py /app/wsgi.py
COPY shared /app/shared

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app", "--workers", "2", "--threads", "4"]
