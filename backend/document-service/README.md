# Document Service

A Flask-based microservice for managing document metadata with CRUD operations, search functionality, and pagination support.

## 🏗️ Architecture

The Document Service is built with a modular architecture:

```
document-service/
├── app.py                 # Main Flask application
├── models/                # Data models and validation
│   ├── document.py        # DocumentModel class
│   └── response.py        # API response structures
├── routes/                # API endpoint handlers
│   └── documents.py       # Document CRUD operations
├── services/              # Business logic layer
│   └── database.py        # Database operations
├── tests/                 # Comprehensive test suite
└── Dockerfile            # Container configuration
```

## 🚀 Features

- **CRUD Operations**: Create, Read, Update, Delete documents
- **Search**: Full-text search across document names and metadata
- **Pagination**: Server-side pagination with configurable page sizes
- **Input Validation**: XSS protection and data sanitization
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Health Monitoring**: Health check endpoint with database connectivity status
- **Logging**: Comprehensive logging for debugging and monitoring

## 📋 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/e2e` | Service availability test |
| `GET` | `/documents` | List all documents with pagination/search |
| `GET` | `/documents/{id}` | Get specific document by ID |
| `POST` | `/documents` | Create new document |
| `PUT` | `/documents/{id}` | Update existing document |
| `DELETE` | `/documents/{id}` | Delete document |

### Query Parameters

#### GET /documents
- `limit` (optional): Number of documents per page (default: all)
- `offset` (optional): Number of documents to skip (default: 0)
- `search` (optional): Search term for document names

**Examples:**
```bash
# Get all documents
GET /documents

# Pagination: Get 15 documents starting from document 30
GET /documents?limit=15&offset=30

# Search: Find documents containing "Financial"
GET /documents?search=Financial

# Combined: Search with pagination
GET /documents?search=Financial&limit=10&offset=0
```

## 📄 API Response Format

All endpoints return consistent JSON responses:

### Success Response
```json
{
  "status": "success",
  "message": "Description of the operation",
  "data": { /* Actual response data */ },
  "timestamp": "2025-08-16T03:00:00.000000"
}
```

### Error Response
```json
{
  "status": "error", 
  "message": "Error description",
  "error": "Detailed error information",
  "timestamp": "2025-08-16T03:00:00.000000"
}
```

### Document Object
```json
{
  "document_id": 1,
  "document_name": "Q3_Financial_Report.pdf",
  "document_type": "PDF",
  "link": "https://storage.example.com/documents/report.pdf",
  "categories": [1, 2, 3],
  "uploaded_by": 1,
  "company": 2,
  "upload_date": "2025-01-15T10:30:00+00:00"
}
```

## 🛠️ Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Access to Supabase database

### Environment Variables
Create a `.env` file with:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DATABASE_URL=your_database_connection_string
```

### Running with Docker

1. **Start the service:**
```bash
cd /path/to/backend
docker-compose up -d document-service
```

2. **Verify it's running:**
```bash
docker ps | grep document-service
curl http://localhost:5003/health
```

3. **View logs:**
```bash
docker logs backend-document-service-1
```

### Local Development

1. **Install dependencies:**
```bash
cd document-service
pip install -r requirements.txt
```

2. **Run the service:**
```bash
python app.py
```

## 🧪 Testing

The document service includes a comprehensive test suite with unit tests, integration tests, and end-to-end tests.

### Test Structure
```
tests/
├── unit/                    # Unit tests for individual components
│   └── test_document_model.py     # DocumentModel validation tests
├── integration/             # Integration tests using Flask test client  
│   ├── test_get_all_documents.py  # Document listing tests
│   └── test_crud_operations.py    # CRUD operation tests
├── e2e/                     # End-to-end tests via HTTP requests
│   ├── test_e2e.py               # Basic service availability tests
│   └── test_full_crud_e2e.py     # Comprehensive workflow tests
├── run_tests.py             # Python test runner
├── pytest.ini              # Pytest configuration
└── README.md               # Detailed test documentation
```

### Running Tests

#### Prerequisites
Ensure the document service is running:
```bash
docker-compose up -d document-service
```

#### Option 1: Run Tests in Container (Recommended)

**Unit Tests:**
```bash
docker exec backend-document-service-1 bash -c "cd /app/tests && python3 unit/test_document_model.py"
```

**Integration Tests:**
```bash
docker exec backend-document-service-1 bash -c "cd /app/tests && python3 -m pytest integration/ -v"
```

**Basic E2E Tests:**
```bash
docker exec backend-document-service-1 bash -c "cd /app/tests && python3 e2e/test_e2e.py"
```

**Full E2E Tests:**
```bash
cd document-service/tests
python3 e2e/test_full_crud_e2e.py
```

#### Option 2: Run Individual Test Types

**Run only unit tests:**
```bash
docker exec backend-document-service-1 bash -c "cd /app/tests && python3 unit/test_document_model.py"
```

**Run only integration tests:**
```bash
docker exec backend-document-service-1 bash -c "cd /app/tests && python3 -m pytest integration/ -v"
```

**Run specific test file:**
```bash
docker exec backend-document-service-1 bash -c "cd /app/tests && python3 -m pytest integration/test_crud_operations.py -v"
```

### Test Coverage

#### What's Tested
- ✅ **DocumentModel**: Validation, sanitization, XSS protection
- ✅ **CRUD Operations**: Create, Read, Update, Delete workflows
- ✅ **Pagination**: Server-side pagination with limit/offset
- ✅ **Search**: Full-text search functionality
- ✅ **Error Handling**: 404s, validation errors, malformed requests
- ✅ **API Consistency**: Response format standardization
- ✅ **Database Integration**: Connection and query operations

#### Expected Results
- **Unit Tests**: All tests should pass
- **Integration Tests**: 13/14 tests pass (1 minor JSON parsing edge case)
- **E2E Tests**: Core functionality tests pass

### Troubleshooting Tests

**Service Not Running:**
```bash
# Check if container is running
docker ps | grep document-service

# Start if not running
docker-compose up -d document-service
```

**Database Connection Issues:**
```bash
# Check service logs
docker logs backend-document-service-1

# Verify health endpoint
curl http://localhost:5003/health
```

**Python Module Errors:**
```bash
# Run tests in container environment where dependencies are installed
docker exec backend-document-service-1 bash -c "cd /app/tests && python3 your_test.py"
```

## 🔧 Configuration

### Database Schema
The service expects the following database structure:

```sql
-- Documents table
CREATE TABLE documents (
    document_id SERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    link TEXT,
    categories INTEGER[],
    uploaded_by INTEGER,
    company INTEGER,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Logging Configuration
Logs are configured at INFO level and include:
- Request/response details
- Database operations
- Error conditions
- Performance metrics

### Security Features
- **Input Sanitization**: All string inputs are sanitized to prevent XSS
- **Validation**: Strict validation for all request data
- **Error Handling**: Secure error messages that don't expose internal details

## 🚀 Production Deployment

### Docker Configuration
The service is configured to run in a Docker container with:
- Python 3.11 Alpine base image
- Health check endpoint monitoring
- Proper signal handling for graceful shutdowns
- Volume mounting for persistent data

### Health Monitoring
Monitor service health via:
```bash
curl http://localhost:5003/health
```

Healthy response:
```json
{
  "status": "success",
  "message": "Document service is healthy",
  "data": {
    "service": "document-service",
    "version": "1.0.0",
    "database_connected": true,
    "timestamp": "2025-08-16T03:00:00.000000"
  }
}
```

### Performance Considerations
- **Pagination**: Always use pagination for large datasets
- **Indexing**: Ensure database indexes on frequently queried fields
- **Caching**: Consider implementing caching for frequently accessed documents

## 🐛 Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check container logs
docker logs backend-document-service-1

# Common causes:
# - Database connection issues
# - Port conflicts
# - Missing environment variables
```

**2. Database Connection Failed**
```bash
# Verify environment variables
docker exec backend-document-service-1 env | grep -E "SUPABASE|DATABASE"

# Test database connectivity
curl http://localhost:5003/health
```

**3. Search Not Working**
```bash
# Test with simple search
curl "http://localhost:5003/documents?search=test"

# Check logs for database query issues
docker logs backend-document-service-1
```

**4. Pagination Issues**
```bash
# Test pagination parameters
curl "http://localhost:5003/documents?limit=5&offset=0"

# Verify total document count
curl "http://localhost:5003/documents"
```

### Debug Mode
Enable debug logging by setting environment variable:
```env
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

## 📈 Future Enhancements

- **File Upload**: Direct file upload support
- **Authentication**: User authentication and authorization
- **Caching**: Redis caching for improved performance
- **Metrics**: Prometheus metrics collection
- **API Versioning**: Support for multiple API versions
- **Rate Limiting**: Request rate limiting
- **Backup**: Automated database backup procedures

## 🤝 Contributing

When contributing to the document service:

1. **Run Tests**: Always run the full test suite before submitting changes
2. **Follow Conventions**: Maintain the existing code structure and naming patterns
3. **Update Documentation**: Update this README for any API changes
4. **Add Tests**: Include tests for new functionality

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test suite output for debugging information
3. Examine service logs: `docker logs backend-document-service-1`
4. Verify health endpoint: `curl http://localhost:5003/health`