# Dynamic Tag Fetching for LLM Service

## Problem
The LLM service used hardcoded tags in `config.py`. Tag changes required code updates and redeployment.

## Solution
LLM service now fetches tags from tag-service on every prediction request.

---

## Changes Made

### 1. `llm-service/tag_client.py` (NEW)
**Why**: HTTP client to fetch tag hierarchy from tag-service

**What**:
- `fetch_hierarchy()` - Calls `GET /tags` endpoint on tag-service
- Returns hierarchy dict: `{"Primary": {"Secondary": ["tertiary"], ...}}`
- 10-second timeout with error handling
- Falls back gracefully if tag-service is unavailable

### 2. `llm-service/config.py`
**Why**: Add tag-service URL configuration

**Changes**:
- Line 33-34: Added `TAG_SERVICE_URL = os.getenv("TAG_SERVICE_URL", "http://tag-service:5007")`
- Line 36: Updated comment - static hierarchy is now fallback only

### 3. `llm-service/hierarchy_validator.py`
**Why**: Make hierarchy updatable at runtime

**Changes**:
- Line 4: Removed static `TAG_HIERARCHY` import
- Line 9-16: Constructor now accepts optional `hierarchy` parameter (defaults to empty dict)
- Line 18-25: Added `set_hierarchy()` method to update hierarchy dynamically

### 4. `llm-service/prediction_service.py`
**Why**: Fetch fresh tags on every prediction request

**Changes**:
- Line 10-12: Import `TagServiceClient` and `Config`
- Line 21: Initialize `self.tag_client = TagServiceClient(Config.TAG_SERVICE_URL)`
- Line 41-53: On each predict request:
  - Fetch hierarchy from tag-service
  - Update validator and prompt generator with fresh tags
  - If fetch fails, use fallback from `config.py`
  - Log success/failure for monitoring

### 5. `docker-compose.yml`
**Why**: Configure LLM service to reach tag-service

**Changes**:
- Line 38-39: Added `depends_on: - tag-service` (ensure tag-service starts first)
- Line 47: Added `TAG_SERVICE_URL=http://tag-service:5007` environment variable

---

## How It Works

1. User makes prediction request to LLM service
2. LLM service calls `tag-service:5007/tags`
3. Tag-service returns latest hierarchy from Supabase
4. LLM updates validator and prompt generator
5. Classification uses current tags

**Fallback**: If tag-service is unreachable, uses static `TAG_HIERARCHY` from config

---

## Deployment

### Docker Compose
Already configured - no changes needed.

### Production
Set environment variable:
```bash
TAG_SERVICE_URL=https://your-tag-service-url
```

---

## Benefits
✅ Tag changes reflect immediately (no redeployment)
✅ Single source of truth (Supabase database)
✅ Resilient (fallback to static config if service down)
✅ Observable (clear logging)
