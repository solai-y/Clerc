# Dynamic Tag Hierarchy Fetching

The LLM service now **dynamically fetches** the tag hierarchy from the tag-service on every prediction request. This ensures that the LLM always uses the latest tags from the Supabase database.

## How It Works

1. **On Every Prediction Request**: The LLM service calls the tag-service to fetch the current tag hierarchy
2. **Hierarchy Update**: The fetched hierarchy is loaded into the validator and prompt generator
3. **Fallback**: If the tag-service is unreachable, it falls back to the static hierarchy in `config.py`

## Architecture

```
LLM Service → Tag Service → Supabase Database
     ↓
  Prompts use latest tags
```

## Configuration

### Environment Variables

The LLM service uses the following environment variable to connect to the tag-service:

```bash
TAG_SERVICE_URL=http://tag-service:5007
```

### For Local Development

If running locally (not in Docker), update your `.env` file:

```bash
TAG_SERVICE_URL=http://localhost:5007
```

### For Deployed Environments

**IMPORTANT**: When deploying to production/staging, ensure the `TAG_SERVICE_URL` environment variable points to your deployed tag-service URL:

```bash
# Example for deployed environment
TAG_SERVICE_URL=https://your-domain.com/tag-service
# OR
TAG_SERVICE_URL=http://your-internal-tag-service:5007
```

## Docker Compose Setup

The `docker-compose.yml` has been updated with:

1. **Service Dependency**: LLM service depends on tag-service
   ```yaml
   llm-service:
     depends_on:
       - tag-service
   ```

2. **Environment Variable**: TAG_SERVICE_URL is set automatically
   ```yaml
   environment:
     - TAG_SERVICE_URL=http://tag-service:5007
   ```

## Files Modified

1. **`tag_client.py`** (new): Client for fetching tags from tag-service
2. **`config.py`**: Added TAG_SERVICE_URL configuration
3. **`hierarchy_validator.py`**: Made hierarchy updatable via `set_hierarchy()`
4. **`prediction_service.py`**: Fetches tags on every prediction request
5. **`docker-compose.yml`**: Added dependency and environment variable

## Benefits

✅ **Always Up-to-Date**: LLM uses latest tags from database
✅ **No Redeployment**: Tag changes reflect immediately
✅ **Fallback Safety**: Uses static config if tag-service is down
✅ **Centralized**: Single source of truth in Supabase

## Deployment Checklist

When deploying to production:

- [ ] Set `TAG_SERVICE_URL` environment variable to your deployed tag-service URL
- [ ] Ensure tag-service is accessible from LLM service (network/firewall rules)
- [ ] Verify Supabase credentials are set in tag-service
- [ ] Test tag fetching with a prediction request
- [ ] Monitor logs for "Successfully loaded tag hierarchy" message

## Testing

To verify dynamic tag fetching is working:

```bash
# 1. Add a new tag via tag-service
curl -X POST http://localhost:5007/tags \
  -H "Content-Type: application/json" \
  -d '{"layer": "primary", "name": "TestCategory"}'

# 2. Make a prediction request to LLM service
# The LLM should now be aware of "TestCategory"

# 3. Check LLM service logs for:
# "Fetching latest tag hierarchy from tag service"
# "Successfully loaded tag hierarchy: X primary, Y secondary, Z tertiary tags"
```

## Monitoring

Watch for these log messages:

- ✅ `"Successfully loaded tag hierarchy"` - Tag fetching succeeded
- ⚠️ `"Failed to fetch tags from tag service: ... Using fallback hierarchy."` - Using static fallback

## Troubleshooting

**Issue**: LLM service can't reach tag-service
**Solution**: Check network connectivity and TAG_SERVICE_URL configuration

**Issue**: Tag changes not reflected in LLM predictions
**Solution**: Verify tag-service is returning updated hierarchy (`GET /tags`)

**Issue**: Using fallback hierarchy
**Solution**: Check tag-service logs and ensure Supabase connection is working
