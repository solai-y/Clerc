# Retraining Service Tests

Comprehensive test suite for the retraining service.

## Test Structure

```
tests/
├── conftest.py                          # Pytest fixtures and configuration
├── pytest.ini                           # Pytest settings
├── requirements.txt                     # Test dependencies
├── unit/                                # Unit tests
│   ├── test_store_text.py              # POST /retraining/store-text tests
│   ├── test_update_tags.py             # POST /retraining/update-tags tests
│   ├── test_get_data.py                # GET /retraining/data/{id} tests
│   ├── test_stats.py                   # GET /retraining/stats tests
│   └── test_health.py                  # GET /health tests
└── integration/                         # Integration tests
    ├── test_full_workflow.py           # Complete workflow tests
    └── test_database_constraints.py    # Database integrity tests
```

## Test Coverage

### Unit Tests (67 test cases)

#### `test_store_text.py` (14 tests)
- ✅ Successful text storage
- ✅ Missing parameters validation
- ✅ Empty text validation
- ✅ Non-existent document handling
- ✅ Multiple text entries per document
- ✅ Large text handling (1MB+)
- ✅ Unicode character support
- ✅ Special character preservation
- ✅ Invalid JSON handling
- ✅ Wrong data types validation

#### `test_update_tags.py` (16 tests)
- ✅ Single hierarchy update
- ✅ Multiple hierarchies update
- ✅ Update without prior text storage
- ✅ Tag replacement (DELETE + INSERT)
- ✅ Text preservation during updates
- ✅ Invalid hierarchy validation
- ✅ Non-existent tag handling
- ✅ Missing hierarchy levels
- ✅ Empty tags array
- ✅ Partial hierarchy validation
- ✅ Parameter validation

#### `test_get_data.py` (9 tests)
- ✅ Successful data retrieval
- ✅ Multiple hierarchies retrieval
- ✅ No data found scenario
- ✅ Text-only entries (no tags)
- ✅ Text preview truncation (>200 chars)
- ✅ Invalid document ID handling
- ✅ Timestamp inclusion
- ✅ Result ordering

#### `test_stats.py` (8 tests)
- ✅ Empty database stats
- ✅ Text-only stats
- ✅ Complete data stats
- ✅ Multiple documents stats
- ✅ Multiple hierarchies per document
- ✅ Average text length calculation
- ✅ Partial tag coverage
- ✅ Response format validation

#### `test_health.py` (3 tests)
- ✅ Health check success
- ✅ Response format validation
- ✅ Root endpoint

### Integration Tests (17 test cases)

#### `test_full_workflow.py` (7 tests)
- ✅ Complete single hierarchy workflow
- ✅ Multiple hierarchy workflow
- ✅ Tag update workflow (user changes tags)
- ✅ Multiple documents workflow
- ✅ Text preservation through workflow
- ✅ Invalid hierarchy graceful failure
- ✅ Stats updates through workflow

#### `test_database_constraints.py` (10 tests)
- ✅ CASCADE delete on document deletion
- ✅ SET NULL on tag deletion
- ✅ Updated_at trigger functionality
- ✅ Foreign key constraint enforcement
- ✅ Multiple rows per document
- ✅ Large text field handling
- ✅ NULL tag IDs allowed
- ✅ Index existence verification

## Running Tests

### Prerequisites

1. **Test Database Setup:**
   ```bash
   # Create test database
   createdb document_classification_test

   # Run schema migration
   psql -d document_classification_test -f ../schema.sql
   ```

2. **Environment Variables:**
   ```bash
   export TEST_DB_HOST=localhost
   export TEST_DB_PORT=5432
   export TEST_DB_NAME=document_classification_test
   export TEST_DB_USER=postgres
   export TEST_DB_PASSWORD=postgres
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_store_text.py

# Specific test class
pytest tests/unit/test_store_text.py::TestStoreText

# Specific test method
pytest tests/unit/test_store_text.py::TestStoreText::test_store_text_success
```

### Run with Coverage

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Failed Tests Only

```bash
pytest --lf  # Last failed
pytest --ff  # Failed first
```

## Test Fixtures

### Database Fixtures
- `test_db`: Session-scoped database connection
- `db_connection`: Function-scoped clean connection
- `clean_db`: Clean database state for each test

### Data Fixtures
- `sample_document_data`: Test document (ID: 9001)
- `sample_tags_hierarchy`: Single tag hierarchy (IDs: 9001-9003)
- `multiple_hierarchies`: Two complete hierarchies (IDs: 9010-9022)
- `sample_text`: Sample document text

### Client Fixture
- `client`: FastAPI TestClient for API requests

## Key Test Scenarios

### 1. Upload Flow Simulation
```python
# Store text after extraction
client.post("/retraining/store-text", json={
    "document_id": 123,
    "text": "extracted text..."
})

# Update tags after user confirmation
client.post("/retraining/update-tags", json={
    "document_id": 123,
    "confirmed_tags": {...}
})
```

### 2. Multiple Hierarchy Handling
Tests verify that documents with multiple primary tags create separate rows:
```
Document 123:
  Row 1: News → Press Release → Q1 Earnings
  Row 2: Disclosure → Financial Report → Annual Report
```

### 3. Tag Update Workflow
Tests verify DELETE + INSERT strategy preserves text:
```
1. Store text
2. Update tags (creates row with tags)
3. Update tags again (deletes old, inserts new)
4. Verify text preserved, tags updated
```

### 4. Database Integrity
Tests verify:
- CASCADE delete when document removed
- SET NULL when tag deleted
- Foreign key constraints enforced
- Triggers update timestamps

## Continuous Integration

### GitHub Actions Example

```yaml
name: Retraining Service Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: document_classification_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend/retraining-service
          pip install -r requirements.txt
          pip install -r tests/requirements.txt

      - name: Run database migrations
        run: |
          psql -h localhost -U postgres -d document_classification_test -f backend/retraining-service/schema.sql
        env:
          PGPASSWORD: postgres

      - name: Run tests
        run: |
          cd backend/retraining-service
          pytest --cov=app --cov-report=xml
        env:
          TEST_DB_HOST: localhost
          TEST_DB_USER: postgres
          TEST_DB_PASSWORD: postgres
          TEST_DB_NAME: document_classification_test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Data Cleanup

All tests use the `clean_db` fixture which:
1. Deletes all retraining_data rows
2. Deletes test documents (ID >= 9000)
3. Deletes test tags (ID >= 9000)
4. Runs before each test
5. Rolls back after each test

## Common Issues

### Issue: "Database connection failed"
**Solution:** Ensure test database exists and environment variables are set correctly.

### Issue: "Foreign key constraint violation"
**Solution:** Check that test fixtures create documents/tags in correct order.

### Issue: "Tests pass individually but fail when run together"
**Solution:** Verify `clean_db` fixture is being used to isolate tests.

### Issue: "Slow test execution"
**Solution:** Consider using pytest-xdist for parallel execution:
```bash
pip install pytest-xdist
pytest -n auto
```

## Writing New Tests

### Example Test Template

```python
def test_new_feature(client, sample_document_data, sample_text, clean_db):
    """Test description"""
    # Arrange
    # ... setup test data

    # Act
    response = client.post("/endpoint", json={...})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'

    # Verify in database
    cursor = clean_db.cursor()
    cursor.execute("SELECT * FROM retraining_data WHERE ...")
    result = cursor.fetchone()
    assert result is not None
```

## Test Metrics

- **Total Tests:** 84
- **Unit Tests:** 67 (80%)
- **Integration Tests:** 17 (20%)
- **Expected Coverage:** >90%
- **Expected Duration:** <30 seconds

## Future Enhancements

- [ ] Performance tests (load testing with 1000+ documents)
- [ ] Concurrency tests (multiple simultaneous updates)
- [ ] Edge case tests (extremely large text, special unicode)
- [ ] API rate limiting tests
- [ ] Error recovery tests
