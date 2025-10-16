# Prediction Service

A microservice orchestrator that intelligently routes document classification requests between AI and LLM services based on confidence thresholds.

## Overview

The Prediction Service acts as an intelligent orchestrator between:
- **AI Service** (Port 5004) - Fast SVM-based hierarchical classification
- **LLM Service** (Port 5005) - Slow but accurate Claude Sonnet 4 classification

## How It Works

1. **Frontend calls prediction service** with document text and confidence thresholds
2. **AI service is called first** (faster, cheaper) for all requested levels
3. **Confidence evaluation** - Check if AI predictions meet thresholds hierarchically
4. **LLM service called if needed** - Only for levels below threshold (and their children)
5. **Response aggregation** - Combine AI and LLM predictions intelligently

## Hierarchical Logic

The service respects the hierarchical nature of classification:

- If **primary** < threshold → LLM processes **primary, secondary, tertiary**
- If **secondary** < threshold → LLM processes **secondary, tertiary** (keeps AI primary)
- If **tertiary** < threshold → LLM processes **tertiary** only

## API Endpoints

### POST `/classify`
Main classification endpoint.

**Request:**
```json
{
  "text": "Apple Inc. announced CEO transition...",
  "predict_levels": ["primary", "secondary", "tertiary"],
  "confidence_thresholds": {
    "primary": 0.90,
    "secondary": 0.85, 
    "tertiary": 0.80
  }
}
```

**Response:**
```json
{
  "prediction": {
    "primary": {
      "pred": "News",
      "confidence": 0.95,
      "source": "ai",
      "ai_prediction": {...},
      "llm_prediction": null
    },
    "secondary": {
      "pred": "Technology", 
      "confidence": 0.92,
      "source": "llm",
      "reasoning": "LLM reasoning...",
      "ai_prediction": {...},
      "llm_prediction": {...}
    }
  },
  "elapsed_seconds": 6.2,
  "processed_text": "processed text...",
  "service_calls": {
    "ai_service": {"called": true, "duration": 2.1, "success": true},
    "llm_service": {"called": true, "duration": 5.8, "success": true, "levels_requested": ["secondary", "tertiary"]}
  },
  "confidence_analysis": {
    "triggered_llm": true,
    "trigger_level": "secondary",
    "levels_below_threshold": ["secondary"]
  }
}
```

### GET `/health`
Health check including downstream services.

### GET `/config`
Current configuration and default thresholds.

## Environment Variables

```bash
# Service URLs
AI_SERVICE_URL=http://ai-service:5004
LLM_SERVICE_URL=http://llm-service:5005

# Default thresholds
DEFAULT_PRIMARY_THRESHOLD=0.90
DEFAULT_SECONDARY_THRESHOLD=0.85
DEFAULT_TERTIARY_THRESHOLD=0.80

# Timeouts
AI_SERVICE_TIMEOUT=30
LLM_SERVICE_TIMEOUT=120
```

## Running the Service

### With Docker Compose
```bash
cd backend
docker-compose up prediction-service
```

### Standalone
```bash
cd backend/prediction-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5006 --reload
```

## Testing

```bash
cd backend/prediction-service

# Run all tests
python -m pytest

# Run specific test types
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/

# With coverage
python -m pytest --cov=. --cov-report=html
```

## Architecture

```
Frontend
    ↓
Nginx (/predict/*)
    ↓
Prediction Service (5006)
    ├── AI Service (5004) - Always called first
    └── LLM Service (5005) - Called if confidence < threshold
```

## File Structure

```
prediction-service/
├── app.py                 # FastAPI main application
├── config.py              # Configuration management
├── models.py              # Pydantic request/response models
├── services/
│   ├── ai_client.py       # AI service client
│   ├── llm_client.py      # LLM service client
│   └── aggregator.py      # Response aggregation logic
├── utils/
│   └── confidence.py      # Confidence evaluation logic
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── requirements.txt
├── Dockerfile
└── README.md
```

## Benefits

1. **Cost Optimization** - Only call expensive LLM when needed
2. **Hierarchical Intelligence** - Respects parent-child classification relationships  
3. **Frontend Control** - Confidence thresholds configurable per request
4. **Performance** - Fast AI service handles most cases
5. **Transparency** - Full visibility into which service provided each prediction
6. **Resilience** - Fallback mechanisms for service failures