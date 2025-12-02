# Clerc API Documentation

This document provides comprehensive API documentation for all Clerc microservices.

## Table of Contents

- [API Gateway](#api-gateway)
- [Document Service](#document-service)
- [Tag Service](#tag-service)
- [AI Service](#ai-service)
- [LLM Service](#llm-service)
- [Prediction Service](#prediction-service)
- [S3 Service](#s3-service)
- [Text Extraction Service](#text-extraction-service)
- [Retraining Service](#retraining-service)
- [Company Service](#company-service)

## Base URLs

### Development
- API Gateway: `http://localhost:8000`
- Direct Services: `http://localhost:500X` (where X is the service port)
- Nginx: `http://localhost`

### Production
- All services: `https://your-domain.com/service-name/`

## Authentication

Most endpoints require Supabase authentication. Include the Supabase JWT token in the Authorization header:

```
Authorization: Bearer <your-supabase-jwt-token>
```

---

## API Gateway

Port: `8000`

The API Gateway routes requests to appropriate microservices.

### Routes

All backend services are accessible through the gateway:

- `/documents/*` → Document Service
- `/tags/*` → Tag Service
- `/ai-service/*` → AI Service
- `/llm-service/*` → LLM Service
- `/predict/*` → Prediction Service
- `/s3/*` → S3 Service
- `/text-extraction/*` → Text Extraction Service
- `/retraining/*` → Retraining Service
- `/companies/*` → Company Service

---

## Document Service

Port: `5002`

Manages document metadata and CRUD operations.

### Endpoints

#### Get All Documents

```http
GET /documents
```

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `tag` (optional): Filter by tag
- `tier` (optional): Filter by tier

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "title": "Document Title",
      "s3_key": "path/to/document.pdf",
      "company_id": "uuid",
      "tags": ["tag1", "tag2"],
      "tier": "tier1",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Document by ID

```http
GET /documents/:id
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Document Title",
  "s3_key": "path/to/document.pdf",
  "company_id": "uuid",
  "tags": ["tag1", "tag2"],
  "tier": "tier1",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Create Document

```http
POST /documents
```

**Request Body:**
```json
{
  "title": "Document Title",
  "s3_key": "path/to/document.pdf",
  "company_id": "uuid",
  "tags": ["tag1", "tag2"],
  "tier": "tier1"
}
```

#### Update Document

```http
PUT /documents/:id
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "tags": ["new_tag1", "new_tag2"],
  "tier": "new_tier"
}
```

#### Delete Document

```http
DELETE /documents/:id
```

#### Get Metrics

```http
GET /documents/metrics
```

**Query Parameters:**
- `start_date` (optional): Start date for metrics
- `end_date` (optional): End date for metrics
- `company_id` (optional): Filter by company

**Response:**
```json
{
  "total_documents": 100,
  "documents_by_tag": {
    "tag1": 50,
    "tag2": 30
  },
  "documents_by_tier": {
    "tier1": 60,
    "tier2": 40
  },
  "upload_trend": [
    {
      "date": "2024-01-01",
      "count": 10
    }
  ]
}
```

---

## Tag Service

Port: `5007`

Manages tag hierarchy and tag operations.

### Endpoints

#### Get All Tags

```http
GET /tags
```

**Response:**
```json
{
  "tags": [
    {
      "id": "uuid",
      "name": "Tag Name",
      "parent_id": null,
      "level": 1,
      "children": [
        {
          "id": "uuid",
          "name": "Child Tag",
          "parent_id": "parent-uuid",
          "level": 2
        }
      ]
    }
  ]
}
```

#### Get Tag by ID

```http
GET /tags/:id
```

#### Create Tag

```http
POST /tags
```

**Request Body:**
```json
{
  "name": "New Tag",
  "parent_id": "uuid" // optional
}
```

#### Update Tag

```http
PUT /tags/:id
```

**Request Body:**
```json
{
  "name": "Updated Tag Name",
  "parent_id": "new-parent-uuid"
}
```

#### Delete Tag

```http
DELETE /tags/:id
```

---

## AI Service

Port: `5004`

Provides AI model predictions for document classification.

### Endpoints

#### Predict Tags

```http
POST /ai-service/predict
```

**Request Body:**
```json
{
  "text": "Document text content",
  "model_version": "latest" // optional
}
```

**Response:**
```json
{
  "predictions": [
    {
      "tag": "tag_name",
      "confidence": 0.95,
      "tier": "tier1"
    }
  ],
  "model_version": "v1.2.0"
}
```

#### Get Model Info

```http
GET /ai-service/model/info
```

**Response:**
```json
{
  "version": "v1.2.0",
  "trained_at": "2024-01-01T00:00:00Z",
  "accuracy": 0.92,
  "total_samples": 10000
}
```

#### Health Check

```http
GET /ai-service/health
```

---

## LLM Service

Port: `5005`

Provides Claude AI integration for document analysis.

### Endpoints

#### Analyze Document

```http
POST /llm-service/analyze
```

**Request Body:**
```json
{
  "text": "Document text content",
  "tags": ["available", "tag", "list"],
  "analysis_type": "classification" // or "extraction"
}
```

**Response:**
```json
{
  "suggested_tags": [
    {
      "tag": "tag_name",
      "reasoning": "Why this tag was suggested",
      "confidence": "high"
    }
  ],
  "summary": "Document summary",
  "extracted_entities": {
    "dates": ["2024-01-01"],
    "amounts": ["$1000"],
    "names": ["Company Name"]
  }
}
```

#### Health Check

```http
GET /llm-service/health
```

---

## Prediction Service

Port: `5006`

Orchestrates predictions using both AI and LLM services.

### Endpoints

#### Predict with Fallback

```http
POST /predict
```

**Request Body:**
```json
{
  "text": "Document text content",
  "company_id": "uuid",
  "use_llm_fallback": true // optional, default: true
}
```

**Response:**
```json
{
  "predictions": [
    {
      "tag": "tag_name",
      "confidence": 0.95,
      "tier": "tier1",
      "source": "ai_model" // or "llm"
    }
  ],
  "processing_time_ms": 150,
  "fallback_used": false
}
```

---

## S3 Service

Port: `5003`

Manages file uploads and downloads to/from AWS S3.

### Endpoints

#### Upload File

```http
POST /s3/upload
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field

**Response:**
```json
{
  "s3_key": "uploads/2024/01/01/filename.pdf",
  "url": "https://bucket.s3.amazonaws.com/uploads/2024/01/01/filename.pdf",
  "size": 1024000
}
```

#### Get File URL

```http
GET /s3/file/:s3_key
```

**Response:**
```json
{
  "url": "https://presigned-url.s3.amazonaws.com/...",
  "expires_in": 3600
}
```

#### Delete File

```http
DELETE /s3/file/:s3_key
```

---

## Text Extraction Service

Port: `5008`

Extracts text from PDF documents.

### Endpoints

#### Extract Text from PDF

```http
POST /text-extraction/extract
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field (PDF)

**Response:**
```json
{
  "text": "Extracted text content from PDF",
  "pages": 10,
  "metadata": {
    "author": "Author Name",
    "created_date": "2024-01-01"
  }
}
```

#### Extract from S3

```http
POST /text-extraction/extract-s3
```

**Request Body:**
```json
{
  "s3_key": "path/to/document.pdf"
}
```

**Response:**
```json
{
  "text": "Extracted text content",
  "pages": 10
}
```

---

## Retraining Service

Port: `5009`

Manages model retraining workflows and training data.

### Endpoints

#### Store Training Data

```http
POST /retraining/store
```

**Request Body:**
```json
{
  "text": "Document text content",
  "tags": ["tag1", "tag2"],
  "company_id": "uuid",
  "document_id": "uuid"
}
```

#### Get Training Data

```http
GET /retraining/data
```

**Query Parameters:**
- `limit` (optional): Number of records to return
- `offset` (optional): Pagination offset
- `company_id` (optional): Filter by company

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "text": "Document text",
      "tags": ["tag1", "tag2"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1000
}
```

#### Update Tags

```http
PUT /retraining/data/:id/tags
```

**Request Body:**
```json
{
  "tags": ["updated_tag1", "updated_tag2"]
}
```

#### Trigger Retraining

```http
POST /retraining/trigger
```

**Request Body:**
```json
{
  "model_type": "hierarchical", // or "flat"
  "min_samples": 100,
  "validation_split": 0.2
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "started",
  "estimated_time_minutes": 30
}
```

#### Get Retraining Status

```http
GET /retraining/status/:job_id
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed", // or "running", "failed"
  "progress": 100,
  "metrics": {
    "accuracy": 0.94,
    "precision": 0.92,
    "recall": 0.91
  },
  "completed_at": "2024-01-01T00:00:00Z"
}
```

#### Get Statistics

```http
GET /retraining/stats
```

**Response:**
```json
{
  "total_training_samples": 10000,
  "samples_by_tag": {
    "tag1": 5000,
    "tag2": 3000
  },
  "last_training": "2024-01-01T00:00:00Z",
  "model_version": "v1.2.0"
}
```

#### Health Check

```http
GET /retraining/health
```

---

## Company Service

Port: `5001`

Manages company data and relationships.

### Endpoints

#### Get All Companies

```http
GET /companies
```

**Response:**
```json
{
  "companies": [
    {
      "id": "uuid",
      "name": "Company Name",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Company by ID

```http
GET /companies/:id
```

#### Create Company

```http
POST /companies
```

**Request Body:**
```json
{
  "name": "New Company Name"
}
```

#### Update Company

```http
PUT /companies/:id
```

**Request Body:**
```json
{
  "name": "Updated Company Name"
}
```

#### Delete Company

```http
DELETE /companies/:id
```

---

## Error Responses

All services follow a consistent error response format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "status": 400
}
```

### Common HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Common Error Codes

- `INVALID_REQUEST`: Malformed request body
- `MISSING_PARAMETER`: Required parameter not provided
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `AUTHENTICATION_REQUIRED`: Authentication token missing
- `PERMISSION_DENIED`: User lacks required permissions
- `MODEL_ERROR`: AI/ML model prediction failed
- `S3_ERROR`: S3 operation failed
- `DATABASE_ERROR`: Database operation failed

---

## Rate Limiting

API Gateway implements rate limiting:

- **Development**: 1000 requests/minute per IP
- **Production**: 100 requests/minute per authenticated user

Exceeding rate limits returns:

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Webhooks

The system supports webhooks for asynchronous events:

### Document Processing Complete

```json
{
  "event": "document.processed",
  "document_id": "uuid",
  "tags": ["tag1", "tag2"],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Model Retrained

```json
{
  "event": "model.retrained",
  "model_version": "v1.2.0",
  "metrics": {
    "accuracy": 0.94
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## SDKs and Client Libraries

Coming soon:
- Python SDK
- JavaScript/TypeScript SDK
- REST API Postman Collection

---

## Support

For API issues or questions:
- Review this documentation
- Check service health endpoints
- Consult [DEPLOYMENT.md](../DEPLOYMENT.md) for troubleshooting
- Open an issue on GitHub
