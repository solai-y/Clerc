# Document Service API Documentation

## Overview

The Document Service is a Flask-based REST API for managing documents. It provides endpoints for CRUD operations on documents with features like pagination, search, filtering, and status management.

**Base URL**: `http://44.200.148.190` (Production) / `http://localhost:5003` (Development)

## Standard API Response Format

All endpoints return responses in a standardized format:

### Success Response
```json
{
  "status": "success",
  "message": "Success message",
  "data": { ... },
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## Authentication

Currently, no authentication is required. CORS is enabled for `http://localhost:3000`.

## Error Codes

| Code | Description |
|------|-------------|
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Request validation failed |
| `INTERNAL_ERROR` | Internal server error |
| `METHOD_NOT_ALLOWED` | HTTP method not allowed |
| `SERVICE_UNHEALTHY` | Service health check failed |

---

## Health and Service Endpoints

### Health Check
Get service health status and database connection.

**Endpoint:** `GET /health`

**Response Example:**
```json
{
  "status": "success",
  "message": "Document service is healthy",
  "data": {
    "service": "document-service",
    "version": "1.0.0",
    "timestamp": "2024-01-01T12:00:00.000000",
    "database_connected": true
  }
}
```

**Error Response (503):**
```json
{
  "status": "error",
  "message": "Document service is unhealthy",
  "error_code": "SERVICE_UNHEALTHY",
  "data": {
    "service": "document-service",
    "version": "1.0.0",
    "database_connected": false,
    "error": "Database connection failed"
  }
}
```

### End-to-End Test
Simple connectivity test endpoint.

**Endpoint:** `GET /e2e`

**Response Example:**
```json
{
  "status": "success",
  "message": "Document service is reachable",
  "data": {
    "service": "document-service"
  }
}
```

### Service Information
Get API overview and available endpoints.

**Endpoint:** `GET /`

**Response Example:**
```json
{
  "status": "success",
  "message": "Document service API",
  "data": {
    "service": "document-service",
    "version": "1.0.0",
    "endpoints": [
      "GET /health - Health check",
      "GET /e2e - End-to-end test",
      "GET /documents - Get all documents",
      "GET /documents/<id> - Get document by ID",
      "POST /documents - Create new document",
      "PUT /documents/<id> - Update document",
      "DELETE /documents/<id> - Delete document",
      "POST /documents/processed - Create processed document entry",
      "PATCH /documents/<id>/tags - Update document tags"
    ]
  }
}
```

---

## Document Endpoints

### Get All Documents
Retrieve documents with optional pagination, search, and filtering.

**Endpoint:** `GET /documents`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Number of documents to return (default: 50) |
| `offset` | integer | No | Number of documents to skip (default: 0) |
| `search` | string | No | Search term for document names |
| `status` | string | No | Filter by status: `uploaded`, `processing`, `processed`, `failed` |
| `company_id` | integer | No | Filter by company ID |

**Example Requests:**
```bash
# Get all documents with default pagination
GET /documents

# Get documents with custom pagination
GET /documents?limit=10&offset=20

# Search for documents
GET /documents?search=invoice

# Filter by status
GET /documents?status=processed

# Filter by company
GET /documents?company_id=123

# Combine filters
GET /documents?limit=5&search=contract&status=processed&company_id=456
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Retrieved 10 of 150 documents",
  "data": {
    "documents": [
      {
        "document_id": 1,
        "document_name": "Invoice_2024_001.pdf",
        "document_type": "invoice",
        "link": "https://storage.example.com/doc1.pdf",
        "upload_date": "2024-01-01T10:00:00.000000",
        "uploaded_by": 101,
        "company": 456,
        "file_size": 1024000,
        "file_hash": "sha256:abc123...",
        "status": "processed"
      }
    ],
    "pagination": {
      "total": 150,
      "page": 1,
      "totalPages": 15,
      "limit": 10,
      "offset": 0
    }
  }
}
```

**Validation Errors (400):**
```json
{
  "status": "error",
  "message": "Validation error: Limit must be greater than 0",
  "error_code": "VALIDATION_ERROR"
}
```

### Get Document by ID
Retrieve a specific document by its ID.

**Endpoint:** `GET /documents/{document_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | integer | Yes | Unique document identifier |

**Example Request:**
```bash
GET /documents/123
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Document retrieved successfully",
  "data": {
    "document_id": 123,
    "document_name": "Contract_2024.pdf",
    "document_type": "contract",
    "link": "https://storage.example.com/contract.pdf",
    "upload_date": "2024-01-15T14:30:00.000000",
    "uploaded_by": 102,
    "company": 789,
    "file_size": 2048000,
    "file_hash": "sha256:def456...",
    "status": "processed"
  }
}
```

**Not Found Response (404):**
```json
{
  "status": "error",
  "message": "Document with ID 123 not found",
  "error_code": "NOT_FOUND"
}
```

### Create Document
Create a new document.

**Endpoint:** `POST /documents`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_name": "New_Document.pdf",
  "document_type": "invoice",
  "link": "https://storage.example.com/new-doc.pdf",
  "uploaded_by": 101,
  "company": 456,
  "file_size": 1024000,
  "file_hash": "sha256:abc123...",
  "upload_date": "2024-01-01T10:00:00.000000",
  "status": "uploaded"
}
```

**Required Fields:**
- `document_name` (string): Name of the document
- `document_type` (string): Type/category of document
- `link` (string): URL or path to the document
- `uploaded_by` (integer): ID of the user who uploaded
- `company` (integer): Company ID

**Optional Fields:**
- `file_size` (integer): File size in bytes
- `file_hash` (string): Hash of the file content
- `upload_date` (string): ISO format timestamp
- `status` (string): Document status (default: "uploaded")

**Valid Status Values:**
- `uploaded` (default)
- `processing`
- `processed`
- `failed`

**Success Response (201):**
```json
{
  "status": "success",
  "message": "Document created successfully",
  "data": {
    "document_id": 124,
    "document_name": "New_Document.pdf",
    "document_type": "invoice",
    "link": "https://storage.example.com/new-doc.pdf",
    "uploaded_by": 101,
    "company": 456,
    "file_size": 1024000,
    "file_hash": "sha256:abc123...",
    "upload_date": "2024-01-01T10:00:00.000000",
    "status": "uploaded"
  }
}
```

**Validation Error (400):**
```json
{
  "status": "error",
  "message": "Validation error: Document name is required; Company ID is required",
  "error_code": "VALIDATION_ERROR"
}
```

### Update Document
Update an existing document.

**Endpoint:** `PUT /documents/{document_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | integer | Yes | Unique document identifier |

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_name": "Updated_Document.pdf",
  "document_type": "contract",
  "link": "https://storage.example.com/updated-doc.pdf",
  "uploaded_by": 101,
  "company": 456,
  "file_size": 2048000,
  "file_hash": "sha256:xyz789...",
  "status": "processed"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Document updated successfully",
  "data": {
    "document_id": 124,
    "document_name": "Updated_Document.pdf",
    "document_type": "contract",
    "link": "https://storage.example.com/updated-doc.pdf",
    "uploaded_by": 101,
    "company": 456,
    "file_size": 2048000,
    "file_hash": "sha256:xyz789...",
    "status": "processed"
  }
}
```

**Not Found Response (404):**
```json
{
  "status": "error",
  "message": "Document with ID 124 not found",
  "error_code": "NOT_FOUND"
}
```

### Delete Document
Delete a document.

**Endpoint:** `DELETE /documents/{document_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | integer | Yes | Unique document identifier |

**Example Request:**
```bash
DELETE /documents/124
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Document deleted successfully",
  "data": null
}
```

**Not Found Response (404):**
```json
{
  "status": "error",
  "message": "Document with ID 124 not found",
  "error_code": "NOT_FOUND"
}
```

### Update Document Status
Update only the status of a document.

**Endpoint:** `PATCH /documents/{document_id}/status`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | integer | Yes | Unique document identifier |

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "processed"
}
```

**Valid Status Values:**
- `uploaded`
- `processing`
- `processed`
- `failed`

**Example Request:**
```bash
PATCH /documents/124/status
Content-Type: application/json

{
  "status": "processing"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Document status updated to 'processing'",
  "data": null
}
```

**Validation Error (400):**
```json
{
  "status": "error",
  "message": "Validation error: Status field is required",
  "error_code": "VALIDATION_ERROR"
}
```

---

## Document Schema

### Document Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_id` | integer | Auto-generated | Unique identifier |
| `document_name` | string | Yes | Document name (max 255 chars) |
| `document_type` | string | Yes | Document type/category (max 255 chars) |
| `link` | string | Yes | URL or path to document (max 255 chars) |
| `upload_date` | string | No | ISO timestamp of upload |
| `uploaded_by` | integer | Yes | User ID who uploaded |
| `company` | integer | Yes | Company ID |
| `file_size` | integer | No | File size in bytes |
| `file_hash` | string | No | File content hash (max 255 chars) |
| `status` | string | No | Processing status (default: "uploaded") |

### Status Lifecycle
```
uploaded → processing → processed
    ↓
  failed
```

---

## Processed Document Endpoints

### Create Processed Document
Create a new processed document entry with empty tag fields for later tag confirmation.

**Endpoint:** `POST /documents/processed`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_id": 123,
  "model_id": 1,
  "threshold_pct": 60,
  "suggested_tags": [
    {"tag": "invoice", "score": 0.95},
    {"tag": "finance", "score": 0.87},
    {"tag": "2024", "score": 0.82}
  ],
  "user_id": 101,
  "ocr_used": false,
  "processing_ms": 1250,
  "request_id": "req_abc123"
}
```

**Required Fields:**
- `document_id` (integer): ID of the raw document

**Optional Fields:**
- `model_id` (integer): ID of the model used for processing
- `threshold_pct` (integer): Confidence threshold percentage (default: 60)
- `suggested_tags` (array): AI-generated tag suggestions with scores
- `user_id` (integer): ID of the user who will review tags
- `ocr_used` (boolean): Whether OCR was used (default: false)
- `processing_ms` (integer): Processing time in milliseconds
- `request_id` (string): Unique request identifier
- `errors` (array): Any processing errors
- `status` (string): Processing status (default: "api_processed")

**Success Response (201):**
```json
{
  "status": "success",
  "message": "Processed document created successfully",
  "data": {
    "process_id": 456,
    "document_id": 123,
    "model_id": 1,
    "threshold_pct": 60,
    "suggested_tags": [
      {"tag": "invoice", "score": 0.95},
      {"tag": "finance", "score": 0.87},
      {"tag": "2024", "score": 0.82}
    ],
    "confirmed_tags": [],
    "user_added_labels": [],
    "user_removed_tags": [],
    "user_reviewed": false,
    "user_id": 101,
    "reviewed_at": null,
    "ocr_used": false,
    "processing_ms": 1250,
    "processing_date": "2024-01-01T10:00:00.000000",
    "status": "api_processed"
  }
}
```

### Update Document Tags
Update confirmed tags, user-added labels, and user-removed tags for a processed document.

**Endpoint:** `PATCH /documents/{document_id}/tags`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | integer | Yes | Raw document ID (not process_id) |

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "confirmed_tags": ["invoice", "finance"],
  "user_added_labels": ["Q1-2024", "urgent"],
  "user_removed_tags": ["2024"],
  "user_id": 101
}
```

**Available Fields:**
- `confirmed_tags` (array): Tags confirmed by user from AI suggestions
- `user_added_labels` (array): Tags manually added by user
- `user_removed_tags` (array): Tags user removed from AI suggestions
- `user_id` (integer): ID of the user making the changes

**Tag Confirmation Workflow:**
1. AI suggests tags in `suggested_tags` with confidence scores
2. User reviews and confirms some tags → `confirmed_tags`
3. User adds new tags not suggested by AI → `user_added_labels`
4. User removes unwanted AI suggestions → `user_removed_tags`
5. System automatically sets `user_reviewed = true` and `reviewed_at = now()`

**Example Request:**
```bash
PATCH /documents/123/tags
Content-Type: application/json

{
  "confirmed_tags": ["invoice", "finance"],
  "user_added_labels": ["urgent", "Q1-2024"],
  "user_removed_tags": ["2024"],
  "user_id": 101
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Document tags updated successfully",
  "data": {
    "process_id": 456,
    "document_id": 123,
    "confirmed_tags": ["invoice", "finance"],
    "user_added_labels": ["urgent", "Q1-2024"],
    "user_removed_tags": ["2024"],
    "user_reviewed": true,
    "user_id": 101,
    "reviewed_at": "2024-01-01T14:30:00.000000",
    "suggested_tags": [
      {"tag": "invoice", "score": 0.95},
      {"tag": "finance", "score": 0.87},
      {"tag": "2024", "score": 0.82}
    ]
  }
}
```

**Not Found Response (404):**
```json
{
  "status": "error",
  "message": "Processed document for document_id 123 not found",
  "error_code": "NOT_FOUND"
}
```

**Validation Error (400):**
```json
{
  "status": "error",
  "message": "Validation error: confirmed_tags must be an array",
  "error_code": "VALIDATION_ERROR"
}
```

---

## Usage Examples

### JavaScript/Frontend Integration
```javascript
const API_BASE = 'http://44.200.148.190';

// Get all documents
const response = await fetch(`${API_BASE}/documents?limit=10&offset=0`);
const data = await response.json();

// Create new document
const newDoc = {
  document_name: "Report_2024.pdf",
  document_type: "report",
  link: "https://storage.example.com/report.pdf",
  uploaded_by: 101,
  company: 456
};

const createResponse = await fetch(`${API_BASE}/documents`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(newDoc)
});

// Update document status
const statusUpdate = await fetch(`${API_BASE}/documents/123/status`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: 'processed' })
});

// Create processed document entry
const processedDoc = {
  document_id: 123,
  suggested_tags: [
    { tag: "invoice", score: 0.95 },
    { tag: "finance", score: 0.87 }
  ],
  user_id: 101
};

const processedResponse = await fetch(`${API_BASE}/documents/processed`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(processedDoc)
});

// Update document tags after user review
const tagUpdate = {
  confirmed_tags: ["invoice"],
  user_added_labels: ["urgent", "Q1-2024"],
  user_removed_tags: ["finance"],
  user_id: 101
};

const tagsResponse = await fetch(`${API_BASE}/documents/123/tags`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(tagUpdate)
});
```

### Python Integration
```python
import requests

API_BASE = 'http://44.200.148.190'

# Get documents with search
response = requests.get(f'{API_BASE}/documents', params={
    'limit': 10,
    'search': 'invoice',
    'status': 'processed'
})
documents = response.json()

# Create document
new_document = {
    'document_name': 'Contract_2024.pdf',
    'document_type': 'contract',
    'link': 'https://storage.example.com/contract.pdf',
    'uploaded_by': 101,
    'company': 456
}

create_response = requests.post(
    f'{API_BASE}/documents',
    json=new_document
)
```

---

## Rate Limiting

Currently no rate limiting is implemented.

## Versioning

API Version: 1.0.0

## Support

For issues or questions about the Document Service API, please refer to the application logs or contact the development team.