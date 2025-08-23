# Testing Setup Guide

This guide explains how to set up and run the complete test suite for the Document Service, including the new tag operations functionality.

## Prerequisites

### 1. Python Dependencies
```bash
# Install required dependencies
pip install flask flask-cors requests pytest python-dotenv

# OR install from requirements file
pip install -r ../requirements.txt
```

### 2. Database Setup
Ensure PostgreSQL is running and accessible. The integration and E2E tests require a working database connection.

### 3. Service Setup
For E2E tests, the Document Service must be running:

```bash
# Navigate to service directory
cd ../..

# Start the service
python app.py
```

**Important**: If you've recently added new code (like tag operations), you must restart the service to pick up the changes.

## Test Categories

### Unit Tests
- **Location**: `unit/`
- **Requirements**: Flask (for tag operations tests)
- **Purpose**: Test individual components in isolation
- **Database**: Uses mocks, no database required

### Integration Tests  
- **Location**: `integration/`
- **Requirements**: Flask, Database connection
- **Purpose**: Test complete workflows with real database
- **Database**: Requires running PostgreSQL instance

### End-to-End Tests
- **Location**: `e2e/`
- **Requirements**: Running Document Service
- **Purpose**: Test complete user scenarios via HTTP
- **Database**: Uses service's database connection

## Running Tests

### Option 1: All Tests
```bash
# Run complete test suite
python run_tests.py --type all

# Run with verbose output
python run_tests.py --type all --verbose
```

### Option 2: Specific Test Types
```bash
# Unit tests only
python run_tests.py --type unit

# Integration tests only
python run_tests.py --type integration

# E2E tests only
python run_tests.py --type e2e
```

### Option 3: Tag-Specific Tests
```bash
# Run all tag-related tests
./test_tag_operations.sh

# Make executable if needed
chmod +x test_tag_operations.sh
```

### Option 4: Individual Test Files
```bash
# Unit tests
python -m pytest unit/test_tag_operations.py -v

# Integration tests
python -m pytest integration/test_tag_operations_integration.py -v

# E2E tests (requires running service)
python e2e/test_tag_operations_e2e.py
```

## Common Issues and Solutions

### Issue 1: Flask Import Error
```
ModuleNotFoundError: No module named 'flask'
```

**Solution**: Install Flask
```bash
pip install flask flask-cors
```

### Issue 2: Tag Endpoints Not Found (404)
```
{"error_code":"NOT_FOUND","message":"Endpoint not found"}
```

**Solution**: Restart the Document Service
```bash
# Stop current service (Ctrl+C)
# Then restart
cd ../.. && python app.py
```

The service needs to be restarted to pick up new endpoint code.

### Issue 3: Database Connection Issues
```
Database service not available
```

**Solution**: Ensure PostgreSQL is running
```bash
# Check if PostgreSQL is running
ps aux | grep postgres

# Or check with docker
docker ps | grep postgres

# Start PostgreSQL if needed
sudo service postgresql start
# OR with docker
docker-compose up -d postgres
```

### Issue 4: Service Not Running (E2E Tests)
```
Connection refused to localhost:5002
```

**Solution**: Start the Document Service
```bash
cd ../..
python app.py
```

## Test Output Examples

### Successful Test Run
```
🏷️  TAG OPERATIONS TEST SUITE
================================

🧪 UNIT TESTS
==============
✅ PASSED: Tag Operations Unit Tests

🔗 INTEGRATION TESTS
====================
✅ PASSED: Tag Operations Integration Tests

🌐 END-TO-END TESTS
===================
✅ Document service is running
✅ Tag endpoints are available
✅ PASSED: Tag Operations E2E Tests

📊 TEST RESULTS SUMMARY
========================
Total tests: 3
Passed: 3
Failed: 0

🎉 ALL TAG TESTS PASSED!
```

### Skipped Tests (Service Restart Needed)
```
🌐 END-TO-END TESTS
===================
✅ Document service is running
⚠️  Tag endpoints not available in running service
The service needs to be restarted to pick up the new tag functionality
To test tag operations:
  1. Stop the current service
  2. Restart with: cd ../.. && python app.py
  3. Run tag tests again
```

### Skipped Tests (Flask Missing)
```
🧪 UNIT TESTS
==============
⚠️  Flask not available - skipping unit tests
Install Flask: pip install flask
```

## Continuous Integration

For CI/CD pipelines, ensure all dependencies are installed:

```yaml
# Example CI configuration
steps:
  - name: Install Dependencies
    run: pip install -r requirements.txt
    
  - name: Start Database
    run: docker-compose up -d postgres
    
  - name: Run Tests
    run: |
      cd backend/document-service/tests
      python run_tests.py --type all
```

## Environment Variables

Optional environment variables for testing:

```bash
# Override service URL for E2E tests
export SERVICE_URL=http://localhost:5002

# Set log level for tests
export LOG_LEVEL=DEBUG
```

## Development Workflow

When developing new tag functionality:

1. **Write tests first** (TDD approach)
2. **Implement functionality**
3. **Restart service** to pick up changes
4. **Run tests** to verify implementation
5. **Update documentation** if needed

## Test Coverage

Current test coverage:
- **28+ test cases** for tag operations
- **Error scenarios**: Invalid data, missing endpoints, database failures
- **Edge cases**: Special characters, unicode, large datasets
- **Performance**: 100+ tags, concurrent operations
- **Workflows**: Complete frontend user journeys

## Troubleshooting Checklist

Before reporting issues, check:

- [ ] Flask is installed (`pip list | grep -i flask`)
- [ ] Database is running and accessible
- [ ] Document Service is running (`curl http://localhost:5002/health`)
- [ ] Service has been restarted after code changes
- [ ] No port conflicts (port 5002 is available)
- [ ] Environment variables are set correctly

## Getting Help

If tests are still failing after following this guide:

1. Check the test output for specific error messages
2. Review the service logs for additional context
3. Verify all prerequisites are met
4. Try running individual test files to isolate issues
5. Check the TAG_TESTING_README.md for detailed test descriptions