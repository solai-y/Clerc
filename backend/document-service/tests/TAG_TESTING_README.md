# Tag Operations Testing Documentation

This document describes the comprehensive test suite for the new tag operations functionality in the Document Service.

## Overview

The tag operations feature allows users to:
- Confirm AI-generated tags
- Add custom user labels
- Remove unwanted tags
- Update tag combinations through the API

## Test Structure

### 1. Unit Tests (`unit/test_tag_operations.py`)

**Purpose**: Test individual components and functions in isolation using mocks.

**Key Test Cases**:
- ✅ Valid confirmed tags update
- ✅ Valid user added labels update
- ✅ Combined tag operations
- ✅ Validation error handling (missing fields, invalid types)
- ✅ Database error handling
- ✅ Document not found scenarios
- ✅ Empty arrays (clearing tags)
- ✅ User removed tags functionality

**How to Run**:
```bash
# From tests directory
python -m pytest unit/test_tag_operations.py -v

# With coverage
python -m pytest unit/test_tag_operations.py -v --cov=routes.documents
```

### 2. Integration Tests (`integration/test_tag_operations_integration.py`)

**Purpose**: Test complete workflows with real database interactions.

**Key Test Cases**:
- ✅ Full workflow: Create document → Create processed entry → Update tags
- ✅ Tag removal workflows
- ✅ Special characters in tags
- ✅ Concurrent tag updates
- ✅ Error scenarios with real database
- ✅ Tag persistence across operations

**How to Run**:
```bash
# From tests directory
python -m pytest integration/test_tag_operations_integration.py -v
```

### 3. End-to-End Tests (`e2e/test_tag_operations_e2e.py`)

**Purpose**: Test complete user scenarios via HTTP requests to running service.

**Key Test Cases**:
- ✅ Tag update endpoint availability
- ✅ Full tag management workflow (frontend perspective)
- ✅ Concurrent operations on multiple documents
- ✅ Various data types and edge cases
- ✅ Comprehensive error handling
- ✅ Performance testing with large datasets
- ✅ Data consistency across operations

**How to Run**:
```bash
# Ensure service is running first
cd ../.. && python app.py &

# Then run tests
python e2e/test_tag_operations_e2e.py
```

## API Endpoint Tested

### PATCH `/documents/{document_id}/tags`

**Request Body**:
```json
{
  "confirmed_tags": ["tag1", "tag2"],           // Optional: AI tags to confirm
  "user_added_labels": ["custom1", "custom2"], // Optional: User custom tags
  "user_removed_tags": ["old1", "old2"]        // Optional: Tags to remove
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Document tags updated successfully",
  "data": {
    "process_id": 123,
    "document_id": 456,
    "confirmed_tags": ["tag1", "tag2"],
    "user_added_labels": ["custom1", "custom2"],
    "suggested_tags": [
      {"tag": "tag1", "score": 0.95},
      {"tag": "tag2", "score": 0.87}
    ],
    // ... other processed document fields
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Test Data Coverage

### Tag Content Types Tested
- ✅ Normal alphanumeric tags
- ✅ Tags with hyphens, underscores, dots
- ✅ Tags with spaces
- ✅ Special characters (@, #, $, &, etc.)
- ✅ Unicode characters (non-English languages)
- ✅ Emoji characters
- ✅ Very long tag names (100+ characters)
- ✅ Empty arrays (clearing tags)

### Error Scenarios Tested
- ✅ Non-existent document ID
- ✅ Document without processed entry
- ✅ Invalid JSON in request body
- ✅ Missing required fields
- ✅ Invalid data types (non-arrays)
- ✅ Database connection failures
- ✅ Concurrent operation conflicts

### Performance Scenarios
- ✅ 100+ tags in single update
- ✅ Concurrent updates to multiple documents
- ✅ Multiple sequential operations
- ✅ Large document datasets

## Running All Tag Tests

### Option 1: Individual Test Suites
```bash
# Unit tests only
python -m pytest unit/test_tag_operations.py -v

# Integration tests only
python -m pytest integration/test_tag_operations_integration.py -v

# E2E tests only (service must be running)
python e2e/test_tag_operations_e2e.py
```

### Option 2: All Tag Tests at Once
```bash
# Run the dedicated tag test script
./test_tag_operations.sh
```

### Option 3: All Tests Including Tags
```bash
# Run complete test suite
python run_tests.py --type all
```

## Frontend Integration Testing

The tests also verify that the API correctly supports the frontend modal functionality:

1. **Initial State**: Document with AI suggestions
2. **User Interaction**: Confirming/rejecting AI tags
3. **Custom Tags**: Adding user-defined labels
4. **Modifications**: Updating existing tag selections
5. **Persistence**: Verifying changes are saved correctly

## Test Environment Setup

### Prerequisites
- Python 3.8+
- Flask application
- PostgreSQL database (for integration tests)
- pytest
- requests library

### Database Setup for Testing
The integration and E2E tests expect:
- A running PostgreSQL instance
- Proper database schema
- Sample test data (created during tests)

### Environment Variables
```bash
# Optional: Override default service URL for E2E tests
export SERVICE_URL=http://localhost:5003
```

## Continuous Integration

These tests are integrated into the CI pipeline:

```yaml
# Example CI configuration
test_tag_operations:
  runs-on: ubuntu-latest
  steps:
    - name: Run Tag Unit Tests
      run: python -m pytest unit/test_tag_operations.py -v
    
    - name: Run Tag Integration Tests
      run: python -m pytest integration/test_tag_operations_integration.py -v
    
    - name: Start Service and Run E2E Tests
      run: |
        python app.py &
        sleep 5
        python e2e/test_tag_operations_e2e.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Ensure you're in the tests directory
   cd backend/document-service/tests
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database service is running
   docker-compose up -d postgres
   ```

3. **Service Not Running (E2E tests)**:
   ```bash
   # Start the document service
   cd ../.. && python app.py
   ```

4. **Port Conflicts**:
   ```bash
   # Check if port 5003 is available
   lsof -i :5003
   ```

### Test Output Examples

**Successful Test Run**:
```
🏷️  TAG OPERATIONS TEST SUITE
================================

🧪 UNIT TESTS
==============
Running: Tag Operations Unit Tests
✅ PASSED: Tag Operations Unit Tests

🔗 INTEGRATION TESTS
====================
Running: Tag Operations Integration Tests
✅ PASSED: Tag Operations Integration Tests

🌐 END-TO-END TESTS
===================
✅ Document service is running
Running: Tag Operations E2E Tests
✅ PASSED: Tag Operations E2E Tests

📊 TEST RESULTS SUMMARY
========================
Total tests: 3
Passed: 3
Failed: 0

🎉 ALL TAG TESTS PASSED!
```

## Contributing

When adding new tag-related functionality:

1. Add unit tests for new functions/methods
2. Add integration tests for new workflows
3. Add E2E tests for new user scenarios
4. Update this documentation
5. Ensure all existing tests still pass

## Test Metrics

Current test coverage for tag operations:
- **Unit Tests**: 15 test cases
- **Integration Tests**: 6 comprehensive workflows
- **E2E Tests**: 7 end-to-end scenarios
- **Total Test Cases**: 28+ individual assertions
- **Coverage**: API endpoints, error handling, edge cases, performance