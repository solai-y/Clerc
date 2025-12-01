# S3 Service

FastAPI-based microservice for file upload and storage to AWS S3.

## Overview

The S3 Service handles secure file uploads to AWS S3, providing a clean API for document storage. It manages file validation, secure filename generation, and S3 bucket operations for the Clerc document management system.

## Key Features

- File upload to AWS S3
- Secure filename sanitization
- File type validation
- Presigned URL generation for secure access
- Automatic file metadata handling

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `POST` | `/upload` | Upload file to S3 |
| `GET` | `/download/{filename}` | Get presigned URL for file download |
| `DELETE` | `/delete/{filename}` | Delete file from S3 |

## Environment Variables

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
S3_BUCKET_NAME=your_bucket_name
```

## Running Locally

**With Docker:**
```bash
cd backend
docker-compose up -d s3-service
```

**Standalone:**
```bash
cd backend/s3-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5003
```

## Service Configuration

- **Port:** 5003
- **Framework:** FastAPI
- **Storage:** AWS S3

## Upload Example

```bash
curl -X POST "http://localhost:5003/upload" \
  -F "file=@document.pdf"
```

## API Documentation

Once running, view interactive API docs at:
- Swagger UI: `http://localhost:5003/docs`
- ReDoc: `http://localhost:5003/redoc`

## Health Check

```bash
curl http://localhost:5003/health
```
