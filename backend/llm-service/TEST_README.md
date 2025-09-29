# LLM Service Testing Guide

This document explains how to test the LLM service to ensure it's working correctly.

## Test Structure

The tests are organized into three categories:

- **Unit Tests** (`tests/unit/`): Test individual components and API endpoints with mocked dependencies
- **Integration Tests** (`tests/integration/`): Test service components working together with mocked external services
- **End-to-End Tests** (`tests/e2e/`): Test the complete service running on port 5005 with real HTTP requests

## Prerequisites

1. **Install test dependencies**:
   ```bash
   cd backend/llm-service/tests
   pip install -r requirements.txt
   ```

2. **For E2E tests**: The LLM service must be running on port 5005:
   ```bash
   cd backend/llm-service
   python main.py
   ```

## Running Tests

### Option 1: Using the Test Runner Script

```bash
cd backend/llm-service/tests

# Install dependencies and run all tests
python run_tests.py --install --all

# Run specific test types
python run_tests.py --unit           # Unit tests only
python run_tests.py --integration    # Integration tests only
python run_tests.py --e2e           # E2E tests only (requires service running)

# Run with coverage reporting
python run_tests.py --unit --coverage
```

### Option 2: Using pytest directly

```bash
cd backend/llm-service/tests

# Run all tests
pytest

# Run specific test categories
pytest unit/                    # Unit tests
pytest integration/            # Integration tests  
pytest e2e/                    # E2E tests

# Run with verbose output
pytest -v

# Run specific test file
pytest unit/test_api_endpoints.py

# Run specific test
pytest unit/test_api_endpoints.py::test_predict_endpoint_success
```

## Test Categories Explained

### Unit Tests (`tests/unit/test_api_endpoints.py`)

Tests the FastAPI endpoints with mocked dependencies:

- ✅ Health check endpoints (`/` and `/health`)
- ✅ Successful prediction requests
- ✅ Partial prediction requests (with context)
- ✅ Error handling (empty text, invalid levels, service errors)
- ✅ Request validation (malformed JSON, missing fields)

**Run with**: `pytest unit/` or `python run_tests.py --unit`

### Integration Tests (`tests/integration/test_prediction_service.py`)

Tests the prediction service with mocked Claude client:

- ✅ Service initialization
- ✅ Full hierarchy prediction (primary → secondary → tertiary)
- ✅ Partial prediction with context
- ✅ Single level prediction
- ✅ Error handling and invalid responses
- ✅ Text preprocessing
- ✅ Timing measurement

**Run with**: `pytest integration/` or `python run_tests.py --integration`

### E2E Tests (`tests/e2e/test_e2e.py`)

Tests the complete service running on port 5005:

- ✅ Service health and availability
- ✅ Complete prediction workflows
- ✅ Real HTTP request/response cycle
- ✅ Performance and timing validation
- ✅ Evidence quality and format
- ✅ Confidence score validation

**Prerequisites**: Service must be running on port 5005
**Run with**: `pytest e2e/` or `python run_tests.py --e2e`

## Expected Test Results

### Unit Tests
- Should always pass (no external dependencies)
- Fast execution (< 10 seconds)
- Tests API validation and error handling

### Integration Tests  
- Should always pass (mocked Claude client)
- Fast execution (< 30 seconds)
- Tests service logic and data flow

### E2E Tests
- **Requires running service on port 5005**
- May take longer if using real LLM calls
- Tests complete integration including AWS Bedrock calls
- May fail if service is not running or configured incorrectly

## Troubleshooting

### E2E Tests Failing

1. **Service not running**: Start the LLM service on port 5005:
   ```bash
   cd backend/llm-service
   python main.py
   ```

2. **Wrong port**: Verify service is on port 5005:
   ```bash
   curl http://localhost:5005/health
   ```

3. **AWS credentials missing**: Ensure AWS credentials are configured:
   ```bash
   # Check environment variables
   echo $AWS_ACCESS_KEY_ID
   echo $AWS_SECRET_ACCESS_KEY
   ```

### Import Errors

If you get import errors, ensure you're running tests from the correct directory:
```bash
cd backend/llm-service/tests
python -m pytest
```

### Dependency Issues

Install/update test dependencies:
```bash
cd backend/llm-service/tests
pip install -r requirements.txt --upgrade
```

## Test Coverage

To run tests with coverage reporting:

```bash
python run_tests.py --unit --coverage
```

This will generate:
- Terminal coverage report
- HTML coverage report in `htmlcov/` directory

## Adding New Tests

1. **Unit tests**: Add to `tests/unit/test_api_endpoints.py`
2. **Integration tests**: Add to `tests/integration/test_prediction_service.py`
3. **E2E tests**: Add to `tests/e2e/test_e2e.py`

Follow the existing patterns and use the fixtures defined in `conftest.py`.

## Continuous Integration

The tests are designed to work in CI/CD pipelines:

- Unit and integration tests require no external services
- E2E tests can be skipped in CI if service is not available
- Use `python run_tests.py --unit --integration` for CI environments