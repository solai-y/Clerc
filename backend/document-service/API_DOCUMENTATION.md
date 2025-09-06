# Document Service API Documentation

## Summary
RESTful API for managing document processing workflows including document upload, AI tagging, user review, and tag management. Supports full CRUD operations with pagination and search capabilities.

**Base URL:** `http://localhost:5002`  
**Content-Type:** `application/json`  
**Authentication:** None (CORS enabled for localhost:3000)

## Quick Reference
- `GET /documents` - List documents with pagination/search
- `GET /documents/{id}` - Get specific document
- `POST /documents/processed` - Create processed document from raw document
- `PATCH /documents/{id}/tags` - Update document tags
- `GET /documents/unprocessed` - Get documents awaiting processing

---

## Standard Response Format
```json
{
  "status": "success|error",
  "message": "Human readable message",
  "data": {...},
  "timestamp": "2025-08-20T02:47:31.682749+00:00"
}
```

---

## Core Endpoints

### Get All Documents
`GET /documents`

**Query Parameters:**
- `limit` (int): Documents to return (default: 50)
- `offset` (int): Skip count for pagination (default: 0) 
- `search` (string): Search document names and tags

**Response Data:**
- `documents[]` - Array of processed documents
- `pagination` - Total count, pages, current page info

### Get Document by ID
`GET /documents/{id}`

Returns single document by document ID.

### Update Document Tags
`PATCH /documents/{id}/tags`

**Request Body:**
```json
{
  "confirmed_tags": ["tag1", "tag2"],
  "user_added_labels": ["manual_tag"],
  "user_removed_tags": ["unwanted_tag"]
}
```

### Create Processed Document
`POST /documents/processed`

Creates processed document entry from raw document.

**Request Body:**
```json
{
  "document_id": 1,
  "suggested_tags": [{"tag": "finance", "score": 0.95}],
  "model_id": 1,
  "threshold_pct": 60
}
```

### Get Unprocessed Documents
`GET /documents/unprocessed?limit=1`

Returns raw documents awaiting AI processing.

---

## Document Structure

### Processed Document
```json
{
  "process_id": 1,
  "document_id": 1,
  "confirmed_tags": ["finance", "report"],
  "suggested_tags": [{"tag": "analysis", "score": 0.85}],
  "user_added_labels": ["priority"],
  "status": "user_confirmed",
  "user_reviewed": true,
  "raw_documents": {
    "document_name": "Report.pdf",
    "document_type": "PDF", 
    "link": "https://storage.example.com/report.pdf",
    "file_size": 1024000,
    "company": 1,
    "companies": {"company_id": 1, "company_name": "Corp"}
  }
}
```

### Key Fields
- **confirmed_tags**: User-approved AI suggestions
- **suggested_tags**: AI recommendations with confidence scores
- **user_added_labels**: Manually added tags
- **status**: `processing`, `user_confirmed`, `error`
- **user_reviewed**: Boolean indicating user review completion

---

## Error Handling
- `200` Success
- `400` Bad Request (invalid input)
- `404` Not Found  
- `500` Internal Server Error

## Notes
- Timestamps in ISO 8601 format
- Tag scores: 0.0 - 1.0 confidence range
- Pagination is 0-indexed
- Search covers document names and all tag types