# Retraining Service

Microservice for storing document text and confirmed tag hierarchies for AI model retraining.

## Overview

This service stores training data in the `retraining_data` table with the following workflow:

1. **After text extraction**: Store document ID + extracted text
2. **After tag confirmation**: Update rows with confirmed tag hierarchies

## Endpoints

### `POST /retraining/store-text`
Store document text for retraining (called after text extraction).

**Request:**
```json
{
  "document_id": 123,
  "text": "extracted document text..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Document text stored for retraining",
  "data": {
    "retraining_id": 1,
    "document_id": 123,
    "text_length": 5000,
    "created_at": "2025-10-24T10:30:00"
  }
}
```

### `POST /retraining/update-tags`
Update retraining data with confirmed tags (called after user confirms tags).

**Request:**
```json
{
  "document_id": 123,
  "confirmed_tags": {
    "tags": [
      {"tag": "News", "level": "primary"},
      {"tag": "Disclosure", "level": "primary"},
      {"tag": "Press Release", "level": "secondary"},
      {"tag": "Financial Report", "level": "secondary"},
      {"tag": "Q1 Earnings", "level": "tertiary"},
      {"tag": "Annual Report", "level": "tertiary"}
    ]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Updated retraining data with 2 tag hierarchies",
  "data": {
    "document_id": 123,
    "hierarchies_count": 2,
    "hierarchies": [
      {
        "retraining_id": 5,
        "hierarchy": "News → Press Release → Q1 Earnings",
        "primary_tag_id": 10,
        "secondary_tag_id": 25,
        "tertiary_tag_id": 42
      },
      {
        "retraining_id": 6,
        "hierarchy": "Disclosure → Financial Report → Annual Report",
        "primary_tag_id": 11,
        "secondary_tag_id": 28,
        "tertiary_tag_id": 45
      }
    ]
  }
}
```

### `GET /retraining/data/<document_id>`
Get all retraining data for a specific document.

### `GET /retraining/stats`
Get statistics about the retraining dataset.

### `GET /health`
Health check endpoint.

## Database Schema

See `schema.sql` for the complete table definition.

**Key points:**
- Multiple rows per document if multiple tag hierarchies exist
- Tag IDs are resolved from the `tags` table
- Hierarchy validation using `tags.parent_id`
- Full document text is stored for retraining

## Environment Variables

```bash
DB_HOST=db
DB_PORT=5432
DB_NAME=document_classification
DB_USER=postgres
DB_PASSWORD=postgres
```

## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

Service runs on port 5009.

## Docker

```bash
docker build -t retraining-service .
docker run -p 5009:5009 retraining-service
```
