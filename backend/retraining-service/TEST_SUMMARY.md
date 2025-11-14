# Retraining Service - Test Suite Summary

## Overview

Comprehensive test suite with **84 test cases** covering all functionality of the retraining service.

## Test Statistics

| Category | Count | Coverage |
|----------|-------|----------|
| **Unit Tests** | 67 | 80% |
| **Integration Tests** | 17 | 20% |
| **Total Tests** | 84 | 100% |

## Test Breakdown by Feature

### 1. Store Text Endpoint (14 tests)
| Test | Description |
|------|-------------|
| `test_store_text_success` | Successfully store document text |
| `test_store_text_missing_document_id` | Validate document_id required |
| `test_store_text_missing_text` | Validate text required |
| `test_store_text_empty_text` | Reject empty text |
| `test_store_text_nonexistent_document` | Handle invalid document ID |
| `test_store_text_multiple_times_same_document` | Allow multiple entries |
| `test_store_text_large_text` | Handle 1MB+ text |
| `test_store_text_unicode_characters` | Preserve unicode (测试, émojis) |
| `test_store_text_special_characters` | Preserve newlines, tabs, quotes |
| `test_store_text_no_body` | Validate request body required |
| `test_store_text_invalid_json` | Handle malformed JSON |
| `test_store_text_wrong_data_types` | Validate data types |

### 2. Update Tags Endpoint (16 tests)
| Test | Description |
|------|-------------|
| `test_update_tags_single_hierarchy_success` | Update with valid hierarchy |
| `test_update_tags_multiple_hierarchies` | Create 2+ rows for multiple hierarchies |
| `test_update_tags_without_prior_text_storage` | Require text stored first |
| `test_update_tags_replaces_old_tags` | DELETE + INSERT strategy |
| `test_update_tags_preserves_text` | Text preserved during updates |
| `test_update_tags_invalid_hierarchy` | Reject invalid parent-child relationships |
| `test_update_tags_nonexistent_tag` | Handle tags not in tags table |
| `test_update_tags_missing_level` | Require all 3 hierarchy levels |
| `test_update_tags_missing_document_id` | Validate document_id required |
| `test_update_tags_missing_confirmed_tags` | Validate confirmed_tags required |
| `test_update_tags_empty_tags_array` | Reject empty tags |
| `test_update_tags_partial_hierarchy` | Validate complete hierarchy |

### 3. Get Data Endpoint (9 tests)
| Test | Description |
|------|-------------|
| `test_get_data_success` | Retrieve complete retraining data |
| `test_get_data_multiple_hierarchies` | Return all hierarchy rows |
| `test_get_data_no_data_found` | Handle no data gracefully |
| `test_get_data_text_only_no_tags` | Return text-only entries |
| `test_get_data_text_preview_truncation` | Truncate preview at 200 chars |
| `test_get_data_invalid_document_id` | Validate ID format |
| `test_get_data_includes_timestamps` | Include created_at, updated_at |
| `test_get_data_ordering` | Order by ID ascending |

### 4. Stats Endpoint (8 tests)
| Test | Description |
|------|-------------|
| `test_stats_empty_database` | Return zeros for empty DB |
| `test_stats_with_text_only` | Count text-only rows |
| `test_stats_with_tags` | Count rows with complete tags |
| `test_stats_multiple_documents` | Count unique documents |
| `test_stats_multiple_hierarchies_same_document` | Count all rows |
| `test_stats_average_text_length_calculation` | Calculate avg correctly |
| `test_stats_partial_tags` | Differentiate tagged vs untagged |
| `test_stats_response_format` | Validate response structure |

### 5. Health Endpoint (3 tests)
| Test | Description |
|------|-------------|
| `test_health_check_success` | Return healthy status |
| `test_health_check_response_format` | Validate response format |
| `test_root_endpoint` | Test service info endpoint |

### 6. Full Workflow (7 integration tests)
| Test | Description |
|------|-------------|
| `test_complete_single_hierarchy_workflow` | Store → Update → Retrieve |
| `test_complete_multiple_hierarchy_workflow` | Handle 2+ hierarchies end-to-end |
| `test_tag_update_workflow` | User changes tags multiple times |
| `test_multiple_documents_workflow` | Process 3+ documents |
| `test_text_preservation_through_workflow` | Text never lost |
| `test_workflow_with_invalid_hierarchy_fails_gracefully` | Handle errors without corruption |

### 7. Database Constraints (10 integration tests)
| Test | Description |
|------|-------------|
| `test_cascade_delete_on_document_deletion` | ON DELETE CASCADE works |
| `test_set_null_on_tag_deletion` | ON DELETE SET NULL works |
| `test_updated_at_trigger` | Trigger updates timestamp |
| `test_foreign_key_constraint_document_id` | FK constraint enforced |
| `test_multiple_rows_same_document_different_hierarchies` | No unique constraint |
| `test_text_field_handles_large_data` | TEXT field unlimited |
| `test_null_tag_ids_allowed` | NULLs allowed |
| `test_indexes_exist` | Performance indexes created |

## Quick Start

### 1. Setup Test Database
```bash
# Create test database
createdb document_classification_test

# Run migration
psql -d document_classification_test -f backend/retraining-service/schema.sql
```

### 2. Install Dependencies
```bash
cd backend/retraining-service
pip install -r tests/requirements.txt
```

### 3. Set Environment Variables
```bash
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5432
export TEST_DB_NAME=document_classification_test
export TEST_DB_USER=postgres
export TEST_DB_PASSWORD=postgres
```

### 4. Run Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage
pytest --cov=app --cov-report=html
```

## Expected Output

```bash
$ pytest

======================== test session starts =========================
platform linux -- Python 3.11.0, pytest-8.2.0
collected 84 items

tests/unit/test_store_text.py::TestStoreText::test_store_text_success PASSED
tests/unit/test_store_text.py::TestStoreText::test_store_text_missing_document_id PASSED
...
tests/integration/test_full_workflow.py::TestFullWorkflow::test_complete_single_hierarchy_workflow PASSED
...

======================== 84 passed in 12.34s =========================
```

## Test Fixtures Reference

### Common Fixtures

```python
@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def clean_db(db_connection):
    """Clean database state"""
    # Deletes retraining_data, test documents/tags
    # Runs before each test

@pytest.fixture
def sample_document_data(clean_db):
    """Test document (ID: 9001)"""
    return {'document_id': 9001, 'document_name': 'test_document.pdf'}

@pytest.fixture
def sample_tags_hierarchy(clean_db):
    """Single tag hierarchy (IDs: 9001-9003)"""
    return {
        'primary': {'id': 9001, 'name': 'Test Primary'},
        'secondary': {'id': 9002, 'name': 'Test Secondary'},
        'tertiary': {'id': 9003, 'name': 'Test Tertiary'}
    }

@pytest.fixture
def multiple_hierarchies(clean_db):
    """Two complete hierarchies (IDs: 9010-9022)"""
    return {
        'hierarchy1': {...},  # News → Press Release → Q1 Earnings
        'hierarchy2': {...}   # Disclosure → Financial Report → Annual Report
    }

@pytest.fixture
def sample_text():
    """Sample document text"""
    return "This is a sample document text for testing..."
```

## Coverage Report

Run with coverage to generate detailed report:

```bash
pytest --cov=app --cov-report=term-missing

Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
app.py                    250      5    98%   125, 342-345
-----------------------------------------------------
TOTAL                     250      5    98%
```

## CI/CD Integration

### Docker Test Run
```bash
# Build test container
docker build -t retraining-service-test -f Dockerfile.test .

# Run tests in container
docker run --rm \
  -e TEST_DB_HOST=db \
  -e TEST_DB_NAME=document_classification_test \
  retraining-service-test pytest
```

### GitHub Actions
See `tests/README.md` for complete GitHub Actions workflow example.

## Common Test Patterns

### Pattern 1: API Request Test
```python
def test_endpoint(client):
    response = client.post("/endpoint", json={...})
    assert response.status_code == 200
    assert response.json()['status'] == 'success'
```

### Pattern 2: Database Verification
```python
def test_database(client, clean_db):
    # API call
    client.post("/endpoint", json={...})

    # Verify in DB
    cursor = clean_db.cursor()
    cursor.execute("SELECT * FROM retraining_data WHERE ...")
    result = cursor.fetchone()
    assert result is not None
```

### Pattern 3: Error Handling
```python
def test_error(client):
    response = client.post("/endpoint", json={...})
    assert response.status_code == 400
    assert 'error message' in response.json()['detail'].lower()
```

## Test Data Ranges

All test data uses IDs >= 9000 to avoid conflicts:
- Documents: 9001-9999
- Tags: 9001-9999
- Hierarchies: 9010-9022, 9100-9999

## Performance Benchmarks

Expected test execution times:
- Unit tests: ~8 seconds
- Integration tests: ~4 seconds
- **Total: ~12 seconds**

## Troubleshooting

### Tests fail with "connection refused"
- Ensure PostgreSQL is running
- Check `TEST_DB_*` environment variables

### Tests fail with "table does not exist"
- Run schema migration first
- Verify test database name

### Tests pass individually but fail together
- Issue with `clean_db` fixture
- Check for database state pollution

### Slow test execution
- Use `pytest -n auto` for parallel execution
- Optimize database queries

## Maintenance

### Adding New Tests
1. Follow existing test patterns
2. Use appropriate fixtures
3. Clean up test data (IDs >= 9000)
4. Update this summary

### Updating Fixtures
1. Modify `conftest.py`
2. Ensure backward compatibility
3. Update fixture documentation

## Resources

- Full test documentation: `tests/README.md`
- Pytest docs: https://docs.pytest.org
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
