# MetricsAnalyticsService Documentation

## Overview

The `MetricsAnalyticsService` calculates two key metrics for the Clerc document classification system:

1. **Top-Tag Accuracy** - Measures how often the AI's highest-confidence predictions match user-confirmed tags
2. **Perfect Match Rate** - Measures how often ALL 3 top tags are accepted together

## Metrics Explained

### 1. Top-Tag Accuracy

**Top-Tag Accuracy** measures the percentage of times that the highest-confidence AI prediction for each hierarchy level (Primary, Secondary, Tertiary) matches the user's final confirmed tag for that level.

#### Formula

```
Top-Tag Accuracy = (# of highest-confidence tags accepted / Total # of highest-confidence tags) × 100
```

#### Example

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

### 2. Perfect Match Rate

**Perfect Match Rate** measures the percentage of documents where ALL 3 highest-confidence tags (Primary, Secondary, Tertiary) were accepted by the user.

#### Formula

```
Perfect Match Rate = (# of documents with all 3 top tags accepted / Total # of documents with all 3 levels) × 100
```

#### Example

Analyzing 3 documents:

**Document 1**:
- Top tags: News, Industry, Healthcare
- User accepted: News ✅, Industry ✅, Healthcare ✅
- **Perfect Match!** ✅

**Document 2**:
- Top tags: Disclosure, SEC_Filings, 10-K
- User accepted: Disclosure ✅, SEC_Filings ✅, 10-Q ❌
- Not a perfect match (2/3 accepted)

**Document 3**:
- Top tags: Recommendations, Analyst_Recommendations, Buy
- User accepted: Recommendations ✅, Analyst_Recommendations ✅, Buy ✅
- **Perfect Match!** ✅

**Result**: Perfect Match Rate = 2/3 = 66.67%

### When to Use Each Metric

| Metric | Best For | Interpretation |
|--------|----------|----------------|
| **Top-Tag Accuracy** | Overall model performance | Shows how accurate your highest-confidence predictions are across all tags |
| **Perfect Match Rate** | User experience quality | Shows how often users can accept all predictions without any changes |

A system with **high Top-Tag Accuracy but low Perfect Match Rate** means predictions are generally good, but users still need to make corrections on most documents.

A system with **high Perfect Match Rate** means users can frequently accept all predictions with zero edits, providing the best user experience.

## Architecture

### Database Schema

The service queries the `processed_documents` table:

```sql
SELECT process_id, document_id, suggested_tags, confirmed_tags, reviewed_at, processing_ms
FROM processed_documents
WHERE confirmed_tags IS NOT NULL
  AND suggested_tags IS NOT NULL
  AND confirmed_tags != '[]'
  AND suggested_tags != '[]'
  AND processing_ms IS NOT NULL
  AND reviewed_at >= start_date_utc (if provided)
  AND reviewed_at <= end_date_utc (if provided)
```

**Filtering Logic:**
- Only includes documents with **non-null** tags
- Excludes documents with **empty arrays** (`[]`) for tags
- Optionally filters by **date range** (using `reviewed_at` column)
- Additional Python-level filtering for nested empty structures like `{tags: []}`

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

Calculate and return Top-Tag Accuracy and Perfect Match Rate metrics.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date in `YYYY-MM-DD` format (Singapore timezone, inclusive) |
| `end_date` | string | No | End date in `YYYY-MM-DD` format (Singapore timezone, inclusive) |

**Date Range Filtering:**
- If both dates provided: Analyzes documents within the date range
- If only `start_date`: Analyzes documents from that date onwards
- If only `end_date`: Analyzes documents up to that date
- If no dates: Analyzes all documents

**Timezone:** All dates are interpreted as Singapore time (UTC+8)

#### Request Examples

**All documents:**
```bash
curl http://localhost:5002/metrics/top-tag-accuracy
```

**Date range:**
```bash
curl "http://localhost:5002/metrics/top-tag-accuracy?start_date=2025-10-20&end_date=2025-10-24"
```

**From date onwards:**
```bash
curl "http://localhost:5002/metrics/top-tag-accuracy?start_date=2025-10-23"
```

**Up to date:**
```bash
curl "http://localhost:5002/metrics/top-tag-accuracy?end_date=2025-10-20"
```

#### Response
```json
{
  "success": true,
  "message": "Metrics calculated - Top-tag accuracy: 85.5% | Perfect match rate: 72.3%",
  "data": {
    "top_tag_accuracy": 85.5,
    "perfect_match_rate": 72.3,
    "top_tag_by_level": {
      "primary": 92.3,
      "secondary": 85.7,
      "tertiary": 78.5
    },
    "total_documents": 150,
    "documents_with_all_levels": 145,
    "perfect_matches": 105,
    "date_range": {
      "start_date": "2025-10-20",
      "end_date": "2025-10-24",
      "timezone": "Asia/Singapore"
    },
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
    },
    "average_timing_s": 4.5,
    "median_timing_s": 4.2,
    "percentile_95_timing_s": 7.8
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `top_tag_accuracy` | float | Overall top-tag accuracy percentage across all levels |
| `perfect_match_rate` | float | Percentage of documents with all 3 top tags accepted |
| `top_tag_by_level.primary` | float | Top-tag accuracy for primary tags |
| `top_tag_by_level.secondary` | float | Top-tag accuracy for secondary tags |
| `top_tag_by_level.tertiary` | float | Top-tag accuracy for tertiary tags |
| `total_documents` | int | Number of documents analyzed |
| `documents_with_all_levels` | int | Number of documents with all 3 hierarchy levels |
| `perfect_matches` | int | Number of documents with all 3 top tags accepted |
| `date_range` | object | Applied date filter (only present if dates provided) |
| `date_range.start_date` | string | Start date filter (YYYY-MM-DD, Singapore timezone) |
| `date_range.end_date` | string | End date filter (YYYY-MM-DD, Singapore timezone) |
| `date_range.timezone` | string | Timezone used for date filtering |
| `average_timing_s` | float |	Average processing time in seconds
| `median_timing_s` |	float	| Median processing time in seconds
| `percentile_95_timing_s`	| float	95th percentile processing time in seconds
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
