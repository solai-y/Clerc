# LLM Document Classification Service

A FastAPI microservice that uses Claude Sonnet 4 via AWS Bedrock for hierarchical document classification.

## Features

- **Context-aware classification**: Supports partial hierarchy prediction
- **Best-fit alternatives**: Automatically fixes invalid predictions using hierarchy validation
- **Retry logic**: Robust error handling with exponential backoff
- **Hierarchical taxonomy**: Primary → Secondary → Tertiary classification levels
- **Evidence generation**: Returns supporting tokens for predictions

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials** in `.env`:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
   ```

3. **Run the service**:
   ```bash
   python main.py
   ```
   
   Or with uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 5005 --reload
   ```

## API Endpoints

### `POST /predict`

Classify a document using the hierarchical taxonomy.

**Request**:
```json
{
  "text": "Document content to classify...",
  "predict": ["primary", "secondary", "tertiary"],
  "context": {
    "primary": "Disclosure"
  }
}
```

**Response**:
```json
{
  "elapsed_seconds": 2.34,
  "processed_text": "Document content...",
  "prediction": {
    "primary": {
      "pred": "Disclosure",
      "confidence": 0.95,
      "key_evidence": {
        "supporting": [
          {"token": "earnings", "impact": "+0.75%"},
          {"token": "report", "impact": "+0.62%"}
        ]
      }
    },
    "secondary": {
      "pred": "Annual_Reports",
      "confidence": 0.90,
      "key_evidence": {
        "supporting": [
          {"token": "annual", "impact": "+0.85%"}
        ]
      },
      "primary": "Disclosure"
    }
  }
}
```

### `GET /health`

Health check endpoint.

## Configuration

The service uses environment variables for configuration:

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key  
- `AWS_REGION`: AWS region (default: us-east-1)
- `CLAUDE_MODEL_ID`: Claude model ID (default: us.anthropic.claude-sonnet-4-20250514-v1:0)
- `MAX_RETRIES`: Maximum retry attempts (default: 5)
- `RETRY_DELAY_SECONDS`: Base retry delay (default: 10)
- `REQUEST_TIMEOUT_SECONDS`: Request timeout (default: 120)

## Architecture

- **`main.py`**: FastAPI application and routes
- **`prediction_service.py`**: Main prediction orchestration
- **`claude_client.py`**: AWS Bedrock client with retry logic
- **`prompt_generator.py`**: Context-aware prompt generation
- **`hierarchy_validator.py`**: Taxonomy validation and best-fit logic
- **`models.py`**: Pydantic request/response models
- **`config.py`**: Configuration management and taxonomy hierarchy

## Integration

This service is designed to integrate with the Clerc orchestrator system. It provides the same API format as the original AI service for seamless replacement.