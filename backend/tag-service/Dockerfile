# backend/tag-service/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# install curl/wget so docker healthchecks work (compose may call wget)
RUN apt-get update && apt-get install -y --no-install-recommends wget curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt

COPY app.py /srv/app.py

EXPOSE 5007
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5007"]
