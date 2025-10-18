# Flask to FastAPI Migration Plan

## Overview
This document outlines the step-by-step plan to migrate all Flask-based microservices to FastAPI. The migration will be done **one service at a time** to ensure stability and avoid breaking changes.

---

## Services to Migrate

### Flask Services (5 total):
1. **company-service** - 28 LOC, 2 endpoints ⭐ *SIMPLEST - START HERE*
2. **s3-service** - 76 LOC, 2 endpoints
3. **ai-service** - 173 LOC, 3 endpoints
4. **text-extraction-service** - 276 LOC, 2 endpoints + error handlers
5. **document-service** - 569 LOC total (136 + 433 routes), 12 endpoints ⚠️ *MOST COMPLEX*

### Already FastAPI:
- **prediction-service** ✅
- **llm-service** ✅

---

## Migration Order (Recommended)

### Phase 1: Simple Services
1. **company-service** - Simplest, good warmup
2. **s3-service** - Simple file upload service

### Phase 2: Medium Complexity
3. **ai-service** - Model prediction service
4. **text-extraction-service** - PDF processing service

### Phase 3: Complex Service
5. **document-service** - Most complex with blueprints and many endpoints

---

## Key Differences: Flask vs FastAPI

### 1. **Application Initialization**
```python
# Flask
from flask import Flask
app = Flask(__name__)

# FastAPI
from fastapi import FastAPI
app = FastAPI()
```

### 2. **Route Decorators**
```python
# Flask
@app.route('/endpoint', methods=['POST', 'GET'])
def handler():
    ...

# FastAPI
@app.post('/endpoint')
@app.get('/endpoint')
async def handler():  # Can be async or sync
    ...
```

### 3. **Request Handling**
```python
# Flask
from flask import request, jsonify
data = request.get_json()
return jsonify({"key": "value"}), 200

# FastAPI
from fastapi import Request
from pydantic import BaseModel

class RequestModel(BaseModel):
    field: str

@app.post('/endpoint')
def handler(request: RequestModel):
    return {"key": "value"}  # Auto JSON conversion
```

### 4. **Error Handling**
```python
# Flask
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

# FastAPI
from fastapi import HTTPException

@app.get('/endpoint')
def handler():
    raise HTTPException(status_code=404, detail="Not found")
```

### 5. **CORS**
```python
# Flask
from flask_cors import CORS
CORS(app)

# FastAPI
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, ...)
```

### 6. **File Uploads**
```python
# Flask
from flask import request
file = request.files['file']

# FastAPI
from fastapi import UploadFile, File
@app.post('/upload')
def upload(file: UploadFile = File(...)):
    ...
```

---

## Changes Required Per Service

### 1. Company-Service
**Complexity:** ⭐ Low
**Endpoints:** 2
**File Structure Changes:**
- Update `app.py` imports and decorators
- Add Pydantic models (minimal)
- Update CORS middleware

**Dependencies to Add:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart  # For form data
```

**Dependencies to Remove:**
```
flask
flask-cors
```

**Test Changes Required:**
- ✅ Change test client from Flask to FastAPI `TestClient`
- ✅ Update fixture imports
- ✅ Response structure stays the same (JSON)

---

### 2. S3-Service
**Complexity:** ⭐ Low
**Endpoints:** 2
**File Structure Changes:**
- Update file upload handling (Flask `request.files` → FastAPI `UploadFile`)
- Add Pydantic models for responses
- Update error handling

**Dependencies to Add:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart
```

**Dependencies to Remove:**
```
flask
werkzeug (partially - may need some utils)
```

**Test Changes Required:**
- ✅ Change test client
- ✅ Update file upload test syntax
- ✅ Multipart form data handling changes

---

### 3. AI-Service
**Complexity:** ⭐⭐ Medium
**Endpoints:** 3
**File Structure Changes:**
- Convert model prediction endpoint
- Add Pydantic models for request/response
- Handle form-data and JSON requests
- Update hot-reload logic if needed

**Dependencies to Add:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart
```

**Dependencies to Remove:**
```
flask
werkzeug
```

**Test Changes Required:**
- ✅ Change test client
- ✅ Update prediction request format
- ✅ Form data tests need updating

---

### 4. Text-Extraction-Service
**Complexity:** ⭐⭐ Medium
**Endpoints:** 2 + error handlers
**File Structure Changes:**
- Update PDF extraction endpoint
- Add Pydantic models
- Convert custom error handlers to FastAPI exception handlers
- Update health check

**Dependencies to Add:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
```

**Dependencies to Remove:**
```
flask
werkzeug (keep for utils if needed)
```

**Test Changes Required:**
- ✅ Change test client
- ✅ Update error handling tests
- ✅ Exception format changes

---

### 5. Document-Service
**Complexity:** ⭐⭐⭐ High
**Endpoints:** 12 (split across routes)
**File Structure Changes:**
- Convert Flask Blueprint → FastAPI APIRouter
- Update all 12 endpoint decorators
- Add comprehensive Pydantic models
- Update database service integration
- Maintain existing response models
- Update CORS configuration

**Files to Update:**
- `app.py` - Main FastAPI app
- `routes/documents.py` - Convert to APIRouter
- `models/document.py` - May need updates
- `models/response.py` - Already has good structure

**Dependencies to Add:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
```

**Dependencies to Remove:**
```
flask
flask-cors
```

**Test Changes Required:**
- ✅ Change test client (affects 66 tests!)
- ✅ Update all fixtures
- ✅ Blueprint routing changes to APIRouter
- ✅ Request/response format validation

---

## Test Migration Changes

### General Test Changes (All Services):

1. **Import Changes:**
```python
# OLD (Flask)
from flask import Flask
from app import app

@pytest.fixture
def client(app):
    return app.test_client()

# NEW (FastAPI)
from fastapi.testclient import TestClient
from app import app

@pytest.fixture
def client():
    return TestClient(app)
```

2. **Request Syntax:**
```python
# OLD (Flask)
response = client.post('/endpoint',
                       data=json.dumps(data),
                       content_type='application/json')

# NEW (FastAPI)
response = client.post('/endpoint', json=data)
```

3. **Response Handling:**
```python
# Both are similar
data = response.json()  # Same in both
assert response.status_code == 200  # Same
```

4. **File Upload Tests:**
```python
# OLD (Flask)
data = {'file': (io.BytesIO(b"content"), 'test.pdf')}
response = client.post('/upload', data=data, content_type='multipart/form-data')

# NEW (FastAPI)
files = {'file': ('test.pdf', io.BytesIO(b"content"), 'application/pdf')}
response = client.post('/upload', files=files)
```

---

## Migration Steps Per Service

### For Each Service (Repeat):

#### Step 1: Create Feature Branch
```bash
git checkout -b migration/flask-to-fastapi-<service-name>
```

#### Step 2: Update Dependencies
- Add FastAPI dependencies to `requirements.txt`
- Remove Flask dependencies
- Run `pip install -r requirements.txt`

#### Step 3: Update Application Code
- Convert `app.py`:
  - Import FastAPI instead of Flask
  - Update route decorators
  - Convert request handling to Pydantic models
  - Update CORS configuration
  - Convert error handlers

#### Step 4: Update Tests
- Update `conftest.py`:
  - Change Flask test client to FastAPI TestClient
- Update all test files:
  - Change request syntax
  - Update file upload tests (if applicable)
  - Verify response assertions still work

#### Step 5: Run Tests Locally
```bash
cd backend/<service-name>
pip install -r requirements.txt
pytest tests/ -v
```

#### Step 6: Update Docker Configuration (if needed)
- Update `Dockerfile` if CMD changes from Flask to Uvicorn:
```dockerfile
# OLD
CMD ["python", "app.py"]
# or
CMD ["flask", "run", "--host=0.0.0.0"]

# NEW
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "<port>"]
```

#### Step 7: Test with Docker Compose
```bash
cd backend
docker compose up -d
docker compose logs <service-name>
# Run integration/e2e tests
pytest <service-name>/tests/ -v
```

#### Step 8: Verify All Services Still Work
- Run full test suite
- Check service health endpoints
- Test inter-service communication

#### Step 9: Commit and Push
```bash
git add .
git commit -m "Migrate <service-name> from Flask to FastAPI"
git push origin migration/flask-to-fastapi-<service-name>
```

#### Step 10: Create Pull Request
- Review changes
- Ensure all CI/CD tests pass
- Merge to dev branch

---

## Dockerfile Changes Required

### Current Pattern (Flask):
```dockerfile
CMD ["python", "app.py"]
# or
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
```

### New Pattern (FastAPI):
```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
# For auto-reload in development:
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
```

---

## Nginx Configuration

**No changes required** - Services still expose the same HTTP endpoints on the same ports.

---

## Risks and Mitigation

### Risks:
1. ❌ Breaking existing API contracts
2. ❌ Test failures due to async/await issues
3. ❌ Performance changes
4. ❌ CORS configuration errors
5. ❌ File upload handling changes

### Mitigation:
1. ✅ Migrate one service at a time
2. ✅ Run full test suite after each migration
3. ✅ Keep response formats identical
4. ✅ Test all endpoints manually after migration
5. ✅ Maintain backward compatibility
6. ✅ Use feature branches and PRs for review

---

## Benefits of Migration

### Performance:
- ⚡ **Async support** - Better for I/O-bound operations
- ⚡ **Lower latency** - FastAPI is generally faster than Flask
- ⚡ **Better concurrency** - Async event loop

### Developer Experience:
- 📝 **Auto-generated OpenAPI docs** - `/docs` endpoint
- 📝 **Type safety** - Pydantic models with validation
- 📝 **Better IDE support** - Type hints everywhere
- 📝 **Modern Python** - Uses latest Python features

### Consistency:
- 🔄 **Unified stack** - All services on same framework
- 🔄 **Easier maintenance** - One framework to learn
- 🔄 **Shared patterns** - Reuse code across services

---

## Estimated Timeline

| Service | Complexity | Est. Time | Dependencies |
|---------|-----------|-----------|--------------|
| company-service | ⭐ Low | 1-2 hours | None |
| s3-service | ⭐ Low | 2-3 hours | company-service done |
| ai-service | ⭐⭐ Medium | 3-4 hours | s3-service done |
| text-extraction-service | ⭐⭐ Medium | 3-4 hours | ai-service done |
| document-service | ⭐⭐⭐ High | 4-6 hours | All others done |

**Total Estimated Time:** 13-19 hours (spread across multiple sessions)

---

## Success Criteria

For each service migration to be considered successful:

- ✅ All existing tests pass
- ✅ No new errors in logs
- ✅ Response formats unchanged
- ✅ CI/CD pipeline passes
- ✅ Manual testing confirms functionality
- ✅ Docker compose integration works
- ✅ Nginx routing still works
- ✅ OpenAPI docs accessible at `/docs`

---

## Rollback Plan

If migration fails for a service:

1. Revert changes in git: `git reset --hard HEAD`
2. Or merge back from main if already committed
3. Redeploy previous version
4. Investigate issues before retry

---

## Notes

- **Async vs Sync**: FastAPI supports both sync and async handlers. Start with sync for easier migration, optimize to async later if needed.
- **Pydantic Models**: Can be optional initially, add them incrementally for better validation.
- **Documentation**: Each service will automatically get OpenAPI docs at `http://service:port/docs`

---

## Ready to Start?

**Recommended first service:** company-service (simplest, only 2 endpoints)

This will serve as a template for the other services.
