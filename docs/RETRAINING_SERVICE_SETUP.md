# Retraining Service Setup Guide

## Overview

A new microservice has been created to store document text and confirmed tag hierarchies for AI model retraining purposes.

## Database Schema

**Table:** `retraining_data`

### Columns:
- `id` - Serial primary key
- `document_id` - Foreign key to `raw_documents.document_id`
- `document_text` - Full extracted text from document
- `primary_tag_id` - Foreign key to `tags.id` (primary classification)
- `secondary_tag_id` - Foreign key to `tags.id` (secondary classification)
- `tertiary_tag_id` - Foreign key to `tags.id` (tertiary classification)
- `created_at` - Timestamp (auto-generated)
- `updated_at` - Timestamp (auto-updated)

### Key Features:
- **Multiple rows per document** if multiple tag hierarchies exist
- **Tag IDs** are stored instead of tag names (resolved from `tags` table)
- **Hierarchy validation** using `tags.parent_id` relationships
- **Cascade delete** when tags or documents are removed

## Service Architecture

**Port:** 5009
**Framework:** FastAPI
**Database:** PostgreSQL (shared with other services)

### Endpoints:

#### `POST /retraining/store-text`
Stores document text after extraction (Step 3 in upload flow).

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

#### `POST /retraining/update-tags`
Updates rows with confirmed tag hierarchies (Step 8 in upload flow).

**Request:**
```json
{
  "document_id": 123,
  "confirmed_tags": {
    "tags": [
      {"tag": "News", "level": "primary"},
      {"tag": "Press Release", "level": "secondary"},
      {"tag": "Q1 Earnings", "level": "tertiary"}
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
      }
    ]
  }
}
```

#### `GET /retraining/data/{document_id}`
Retrieves all retraining rows for a specific document.

#### `GET /retraining/stats`
Returns statistics about the retraining dataset.

#### `GET /health`
Health check endpoint.

## Integration Points

### 1. Upload Flow (upload-modal.tsx)

**After text extraction (Step 3.5):**
```typescript
await fetch('/api/retraining/store-text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id: documentId,
    text: documentText
  })
})
```

**After tag confirmation (Step 8):**
```typescript
await fetch('/api/retraining/update-tags', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id: parseInt(documentId),
    confirmed_tags: confirmedTagsData.confirmed_tags
  })
})
```

### 2. Tag Update Flow (hierarchy-based-confirm-tags-modal.tsx)

When users modify tags from the document table:
```typescript
await fetch('/api/retraining/update-tags', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    document_id: parseInt(document.id),
    confirmed_tags: confirmedTagsData.confirmed_tags
  })
})
```

### 3. Document Service (document-service/routes/documents.py)

**PATCH /documents/{document_id}/tags endpoint:**
- Automatically calls retraining service when tags are updated
- Uses `httpx` for async HTTP requests
- Non-blocking (errors are logged but don't fail the main request)

```python
async with httpx.AsyncClient(timeout=10.0) as client:
    retraining_response = await client.post(
        f"{retraining_url}/retraining/update-tags",
        json={
            "document_id": document_id,
            "confirmed_tags": data['confirmed_tags']
        }
    )
```

## Data Flow

### Upload Process:
```
1. User uploads PDF → S3
2. Create raw_documents entry
3. Extract text from PDF
   ↳ 3.5. Call retraining service: store text
4. Classify text (AI/LLM)
5. Create processed_documents entry
6. Show confirmation modal
7. User reviews/modifies tags
8. User confirms → PATCH /documents/{id}/tags
   ↳ 8.5. Call retraining service: update tags
```

### Tag Hierarchy Resolution:

The service traces hierarchy paths using the `tags.parent_id` relationship:

**Example:**
- Tertiary: "Q1 Earnings" (id: 42, parent_id: 25)
- Secondary: "Press Release" (id: 25, parent_id: 10)
- Primary: "News" (id: 10, parent_id: null)

**Result:** One row with IDs (10, 25, 42)

### Multiple Hierarchies:

If a document has:
- Primary: ["News", "Disclosure"]
- Secondary: ["Press Release", "Financial Report"]
- Tertiary: ["Q1 Earnings", "Annual Report"]

The service creates **2 rows**:
1. News → Press Release → Q1 Earnings
2. Disclosure → Financial Report → Annual Report

## Deployment

### Docker Setup:

The service is already added to `docker-compose.yml`:

```yaml
retraining-service:
  build: ./retraining-service
  ports:
    - "5009:5009"
  env_file:
    - .env
  environment:
    - DB_HOST=${DB_HOST}
    - DB_PORT=${DB_PORT}
    - DB_NAME=${DB_NAME}
    - DB_USER=${DB_USER}
    - DB_PASSWORD=${DB_PASSWORD}
```

### Nginx Configuration:

Route added at `/retraining/*`:

```nginx
location ^~ /retraining/ {
  proxy_pass http://retraining_service/retraining/;
  proxy_http_version 1.1;
  proxy_read_timeout 60s;
  # ... CORS headers
}
```

### API Gateway:

Service registered in `api-gateway/main.py`:

```python
SERVICES = {
    # ... other services
    "retraining-service": "http://retraining-service:5009",
}
```

## Database Migration

Run this SQL to create the table:

```bash
psql -h localhost -U postgres -d document_classification -f backend/retraining-service/schema.sql
```

Or manually execute the SQL from `backend/retraining-service/schema.sql`.

## Testing

### 1. Health Check:
```bash
curl http://localhost/retraining/health
```

### 2. Get Statistics:
```bash
curl http://localhost/retraining/stats
```

### 3. Get Document Data:
```bash
curl http://localhost/retraining/data/123
```

## Error Handling

All retraining service calls are **non-blocking** and **non-critical**:
- If the service is down, document upload/tagging still succeeds
- Errors are logged with `console.warn()` in frontend
- Backend logs warnings but doesn't throw exceptions

This ensures the main workflow is never interrupted by retraining service issues.

## Files Created/Modified

### New Files:
- `/backend/retraining-service/app.py` - FastAPI service
- `/backend/retraining-service/schema.sql` - Database schema
- `/backend/retraining-service/Dockerfile` - Container config
- `/backend/retraining-service/requirements.txt` - Python dependencies
- `/backend/retraining-service/README.md` - Service documentation

### Modified Files:
- `/backend/docker-compose.yml` - Added retraining-service
- `/backend/nginx/nginx.conf` - Added /retraining/* route
- `/backend/api-gateway/main.py` - Added service to SERVICES dict
- `/backend/document-service/routes/documents.py` - Added retraining call on tag updates
- `/frontend/components/upload-modal.tsx` - Added retraining calls on upload
- `/frontend/components/hierarchy-based-confirm-tags-modal.tsx` - Added retraining call on tag confirmation

## Next Steps

1. **Run database migration** to create the `retraining_data` table
2. **Build and start services:**
   ```bash
   cd backend
   docker-compose up --build retraining-service
   ```
3. **Test the integration** by uploading a document and confirming tags
4. **Query the data:**
   ```sql
   SELECT
     rd.id,
     rd.document_id,
     pt.tag_name as primary_tag,
     st.tag_name as secondary_tag,
     tt.tag_name as tertiary_tag,
     LENGTH(rd.document_text) as text_length
   FROM retraining_data rd
   LEFT JOIN tags pt ON rd.primary_tag_id = pt.id
   LEFT JOIN tags st ON rd.secondary_tag_id = st.id
   LEFT JOIN tags tt ON rd.tertiary_tag_id = tt.id;
   ```

## Monitoring

Check service logs:
```bash
docker-compose logs -f retraining-service
```

Look for:
- `✅ Retraining text stored`
- `✅ Retraining tags updated`
- `⚠️ Retraining ... failed (non-critical)` (if service is having issues)
