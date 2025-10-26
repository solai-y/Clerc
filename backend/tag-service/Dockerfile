# backend/tag-service/Dockerfile
FROM python:3.11-slim

WORKDIR /srv

# Build tools (small) for any wheels; remove cache afterwards
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# your service
COPY app.py /srv/app.py

ENV PORT=5007
ENV HOST=0.0.0.0

EXPOSE 5007
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5007"]
