# MetricsAnalyticsService Documentation

## Overview

The `MetricsAnalyticsService` calculates **Top-Tag Accuracy** metrics for the Clerc document classification system. This service measures how often the AI's highest-confidence predictions match the final user-confirmed tags.

## What is Top-Tag Accuracy?

**Top-Tag Accuracy** measures the percentage of times that the highest-confidence AI prediction for each hierarchy level (Primary, Secondary, Tertiary) matches the user's final confirmed tag for that level.

### Formula

```
Top-Tag Accuracy = (# of highest-confidence tags accepted / Total # of highest-confidence tags) × 100
```

### Example

For a document:
- **Suggested Tags (AI predictions)**:
  - Primary: "News" (95% confidence), "Disclosure" (80% confidence)
  - Secondary: "Industry" (90% confidence), "Company" (85% confidence)
  - Tertiary: "Healthcare" (88% confidence), "Energy" (82% confidence)

- **Confirmed Tags (User approved)**:
  - Primary: "News"
  - Secondary: "Industry"
  - Tertiary: "Energy"

**Analysis**:
- ✅ Primary: "News" (highest confidence) was accepted → 1/1
- ✅ Secondary: "Industry" (highest confidence) was accepted → 1/1
- ❌ Tertiary: "Healthcare" (highest confidence) was rejected, user chose "Energy" → 0/1

**Result**: Top-Tag Accuracy = 2/3 = 66.67%

## Architecture

### Database Schema

The service queries the `processed_documents` table:

```sql
SELECT process_id, document_id, suggested_tags, confirmed_tags
FROM processed_documents
WHERE confirmed_tags IS NOT NULL
  AND suggested_tags IS NOT NULL
```

### Data Structures

#### `suggested_tags` (JSONB)
Contains AI predictions with confidence scores:

```json
[
  {
    "tag": "News",
    "hierarchy_level": "primary",
    "score": 0.95,
    "source": "ai"
  },
  {
    "tag": "Industry",
    "hierarchy_level": "secondary",
    "score": 0.90,
    "source": "ai"
  }
]
```

Or nested structure:
```json
{
  "tags": [...]
}
```

#### `confirmed_tags` (JSONB)
Contains user-approved tags:

```json
{
  "tags": [
    {
      "tag": "News",
      "level": "primary",
      "source": "ai",
      "confidence": 0.95
    },
    {
      "tag": "Industry",
      "level": "secondary",
      "source": "ai",
      "confidence": 0.90
    }
  ]
}
```

## API Endpoint

### `GET /metrics/top-tag-accuracy`

Calculate and return Top-Tag Accuracy metrics.

#### Request
```bash
curl http://localhost:5002/metrics/top-tag-accuracy
```

#### Response
```json
{
  "success": true,
  "message": "Top-tag accuracy calculated: 85.5%",
  "data": {
    "overall_accuracy": 85.5,
    "by_level": {
      "primary": 92.3,
      "secondary": 85.7,
      "tertiary": 78.5
    },
    "total_documents": 150,
    "metrics": {
      "primary": {
        "accepted": 138,
        "total": 150
      },
      "secondary": {
        "accepted": 128,
        "total": 150
      },
      "tertiary": {
        "accepted": 117,
        "total": 150
      }
    }
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `overall_accuracy` | float | Overall accuracy percentage across all levels |
| `by_level.primary` | float | Accuracy for primary tags |
| `by_level.secondary` | float | Accuracy for secondary tags |
| `by_level.tertiary` | float | Accuracy for tertiary tags |
| `total_documents` | int | Number of documents analyzed |
| `metrics.*.accepted` | int | Number of top-confidence tags accepted |
| `metrics.*.total` | int | Total number of top-confidence tags suggested |

## Implementation Details

### Service Class: `MetricsAnalyticsService`

Located in: `services/metrics_analytics.py`

#### Main Method: `calculate_top_tag_accuracy()`

**Process Flow**:

1. **Fetch Documents**: Query all documents with both `suggested_tags` and `confirmed_tags`
2. **For Each Document**:
   - Extract highest-confidence tag for each level from `suggested_tags`
   - Extract user-confirmed tags for each level from `confirmed_tags`
   - Compare top-confidence tags against confirmed tags
   - Update acceptance counters
3. **Calculate Metrics**: Compute accuracy percentages for each level and overall

#### Helper Methods

##### `_get_top_confidence_tags_by_level(suggested_tags)`
Extracts the highest confidence tag for each hierarchy level.

**Parameters**:
- `suggested_tags`: List or dict containing AI predictions

**Returns**:
```python
{
  'primary': {'tag': 'News', 'confidence': 0.95, 'source': 'ai'},
  'secondary': {'tag': 'Industry', 'confidence': 0.90, 'source': 'ai'},
  'tertiary': {'tag': 'Healthcare', 'confidence': 0.88, 'source': 'ai'}
}
```

##### `_get_confirmed_tags_by_level(confirmed_tags)`
Extracts confirmed tags grouped by level.

**Parameters**:
- `confirmed_tags`: List or dict containing user-confirmed tags

**Returns**:
```python
{
  'primary': ['News'],
  'secondary': ['Industry', 'Company'],
  'tertiary': ['Energy']
}
```

## Usage

### Testing the Service

Run the test script inside the Docker container:

```bash
docker exec -it document-service python test_metrics.py
```

### Using in Code

```python
from services.metrics_analytics import MetricsAnalyticsService

# Initialize service
service = MetricsAnalyticsService()

# Calculate metrics
result = service.calculate_top_tag_accuracy()

print(f"Overall Accuracy: {result['overall_accuracy']}%")
print(f"Primary: {result['by_level']['primary']}%")
print(f"Secondary: {result['by_level']['secondary']}%")
print(f"Tertiary: {result['by_level']['tertiary']}%")
```

## Error Handling

The service handles various error cases:

1. **No Documents**: Returns zero accuracy if no documents found
2. **Missing Fields**: Skips documents with missing `suggested_tags` or `confirmed_tags`
3. **Invalid Structure**: Logs warnings and continues processing
4. **Database Errors**: Raises exception with descriptive error message

## Logging

The service logs important events:

- INFO: Document counts, accuracy calculations
- DEBUG: Individual tag acceptance/rejection decisions
- WARNING: Data parsing issues, missing fields
- ERROR: Database errors, calculation failures

## Performance Considerations

- Fetches all relevant documents in a single query
- Processes documents in memory (efficient for typical dataset sizes)
- Uses set operations for fast tag lookups
- No N+1 query problems

## Future Enhancements

Potential improvements:

1. **Time-based Analysis**: Track accuracy over time periods
2. **Confidence Thresholds**: Filter by minimum confidence levels
3. **Source-specific Metrics**: Separate accuracy for AI vs LLM predictions
4. **Per-tag Metrics**: Track which specific tags are most/least accurate
5. **Caching**: Cache results with invalidation on new confirmations
6. **Batch Processing**: Process documents in batches for very large datasets

## Testing

### Manual Testing

1. Ensure you have documents with both `suggested_tags` and `confirmed_tags`
2. Call the API endpoint: `GET /metrics/top-tag-accuracy`
3. Verify the response contains expected accuracy values

### Integration Testing

Add to your test suite:

```python
def test_top_tag_accuracy():
    from services.metrics_analytics import MetricsAnalyticsService

    service = MetricsAnalyticsService()
    result = service.calculate_top_tag_accuracy()

    assert 'overall_accuracy' in result
    assert 'by_level' in result
    assert result['overall_accuracy'] >= 0
    assert result['overall_accuracy'] <= 100
```

## Troubleshooting

### Issue: Zero accuracy returned
**Solution**: Check that documents have both `suggested_tags` and `confirmed_tags` populated

### Issue: Service initialization fails
**Solution**: Verify `SUPABASE_URL` and `SUPABASE_KEY` environment variables are set

### Issue: Accuracy seems incorrect
**Solution**: Check the data format in `suggested_tags` and `confirmed_tags` matches expected structure

## Related Files

- `services/metrics_analytics.py` - Service implementation
- `routes/metrics.py` - API route handler
- `app.py` - Router registration
- `test_metrics.py` - Test script
