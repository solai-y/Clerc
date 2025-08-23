# Document Service Test Suite

Comprehensive test suite for the Document Service including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_document_model.py     # DocumentModel class tests
│   └── __init__.py
├── integration/             # Integration tests using Flask test client
│   ├── test_get_all_documents.py  # Basic document listing tests
│   ├── test_crud_operations.py    # Full CRUD operation tests
│   ├── test_missing_endpoints.py  # Tests for root and status update endpoints
│   └── __init__.py
├── e2e/                     # End-to-end tests via HTTP requests
│   ├── test_e2e.py                     # Basic service availability tests
│   ├── test_nginx_e2e.py               # Nginx routing tests
│   ├── test_full_crud_e2e.py           # Comprehensive E2E tests
│   └── test_missing_endpoints_e2e.py   # E2E tests for previously untested endpoints
├── run_tests.py             # Test runner script
├── README.md               # This file
└── pytest.ini             # Pytest configuration
```

## Running Tests

### Quick Start

Make sure the document service is running:
```bash
cd /mnt/c/Users/abhay/Documents/Clerc/backend
docker-compose up -d document-service
```

Then run all tests:
```bash
cd document-service/tests
python run_tests.py
```

### Test Types

#### 1. Unit Tests
Test individual components in isolation:
```bash
python run_tests.py --type unit
```

**What it tests:**
- DocumentModel validation and sanitization
- String length limits and XSS protection
- Date and integer validation
- Model to dictionary conversion

#### 2. Integration Tests  
Test components working together using Flask test client:
```bash
python run_tests.py --type integration
```

**What it tests:**
- All CRUD operations (Create, Read, Update, Delete)
- Pagination and search functionality
- Input validation and error handling
- API response structure consistency

#### 3. End-to-End Tests
Test the complete service via HTTP requests:
```bash
python run_tests.py --type e2e
```

**What it tests:**
- Service availability and health checks
- Complete document lifecycle (CRUD)
- Error scenarios (404, validation errors, etc.)
- Concurrent operations
- API response consistency across all endpoints

### Individual Test Commands

#### Using pytest (for integration tests):
```bash
# Run all integration tests
python -m pytest integration/ -v

# Run specific test file
python -m pytest integration/test_crud_operations.py -v

# Run specific test method
python -m pytest integration/test_crud_operations.py::TestDocumentCRUD::test_create_document_valid -v
```

#### Running individual test files:
```bash
# Unit tests
python unit/test_document_model.py

# Basic E2E tests  
python e2e/test_e2e.py

# Comprehensive E2E tests
python e2e/test_full_crud_e2e.py
```

## Test Configuration

### Environment Variables
- `SERVICE_URL`: Base URL for E2E tests (default: http://localhost:5002)

### Prerequisites
1. **Service Running**: Document service must be running on port 5002
2. **Database Access**: Service needs access to Supabase database
3. **Test Data**: Some tests expect existing documents in the database

### Test Data Requirements

The tests expect:
- At least one document with ID 1 in the database
- Documents containing "Financial" in the name (for search tests)
- Valid user IDs (1) and company IDs (1) for creating test documents

## Test Coverage

### API Endpoints Tested
- ✅ `GET /` - Root endpoint with API information
- ✅ `GET /e2e` - Service availability
- ✅ `GET /health` - Health check
- ✅ `GET /documents` - List all documents
- ✅ `GET /documents?limit=N&offset=N` - Pagination
- ✅ `GET /documents?search=term` - Search
- ✅ `GET /documents?status=X` - Filter by status
- ✅ `GET /documents?company_id=X` - Filter by company
- ✅ `GET /documents/{id}` - Get specific document
- ✅ `POST /documents` - Create document
- ✅ `PUT /documents/{id}` - Update document  
- ✅ `DELETE /documents/{id}` - Delete document
- ✅ `PATCH /documents/{id}/status` - Update document status

### Error Scenarios Tested
- ✅ 404 Not Found (non-existent documents)
- ✅ 400 Bad Request (validation errors)
- ✅ 400 Bad Request (invalid JSON)
- ✅ 405 Method Not Allowed
- ✅ Input sanitization (XSS prevention)

### Business Logic Tested
- ✅ Document model validation
- ✅ CRUD operations
- ✅ Search functionality
- ✅ Pagination
- ✅ Concurrent operations
- ✅ Data consistency

## Troubleshooting

### Common Issues

1. **Service Not Running**
   ```
   Error: connect ECONNREFUSED 127.0.0.1:5002
   ```
   **Solution**: Start the document service:
   ```bash
   docker-compose up -d document-service
   ```

2. **Database Connection Issues**
   ```
   Error: Database service not available
   ```
   **Solution**: Check service logs and environment variables:
   ```bash
   docker logs backend-document-service-1
   ```

3. **Import Errors in Tests**
   ```
   ModuleNotFoundError: No module named 'models'
   ```
   **Solution**: Run tests from the tests directory or use the test runner

### Debugging Tests

Enable verbose output:
```bash
python run_tests.py --verbose
```

Run individual test methods for detailed debugging:
```bash
python -m pytest integration/test_crud_operations.py::TestDocumentCRUD::test_create_document_valid -v -s
```

## Adding New Tests

### Unit Tests
Add new test files in `unit/` directory following the pattern:
```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from your_module import YourClass

class TestYourClass:
    def test_your_method(self):
        # Test implementation
        pass
```

### Integration Tests  
Add test methods to existing files or create new files in `integration/`:
```python
def test_your_endpoint(self, client: FlaskClient):
    response = client.get('/your-endpoint')
    assert response.status_code == 200
    # Additional assertions
```

### E2E Tests
Add test methods to `e2e/test_full_crud_e2e.py` or create new E2E test files:
```python
def test_your_scenario(self):
    response = requests.get(f"{self.base_url}/your-endpoint")
    assert response.status_code == 200
    # Additional assertions
```

## Test Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: E2E tests clean up created resources
3. **Assertions**: Use descriptive assertion messages
4. **Coverage**: Test both happy path and error scenarios
5. **Documentation**: Add docstrings explaining what each test verifies