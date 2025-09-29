# Document Classification Orchestrator Service Design

## Overview

This document outlines the design for implementing an orchestrator service that sits between the frontend and the classification services (AI service and LLM service). The orchestrator will intelligently route classification requests based on confidence thresholds and aggregate responses from multiple services.

## Current Architecture Analysis

### Existing Services
1. **AI Service** (Port 5004) - SVM-based hierarchical classification
   - Endpoint: `/predict`
   - Response format:
     ```json
     {
       "prediction": {
         "primary": {"pred": "...", "confidence": 0.85},
         "secondary": {"pred": "...", "confidence": 0.80},
         "tertiary": {"pred": "...", "confidence": 0.75}
       },
       "elapsed_seconds": 2.5,
       "processed_text": "..."
     }
     ```

2. **LLM Service** (Port 5005) - Claude Sonnet 4 classification
   - Endpoint: `/predict`
   - Response format:
     ```json
     {
       "elapsed_seconds": 5.35,
       "prediction": {
         "primary": {"pred": "...", "confidence": 0.98, "reasoning": "..."},
         "secondary": {"pred": "...", "confidence": 0.95, "reasoning": "..."},
         "tertiary": {"pred": "...", "confidence": 0.92, "reasoning": "..."}
       },
       "processed_text": "..."
     }
     ```

3. **Frontend** - Next.js application
   - Current API calls go directly to individual services via nginx proxy
   - No current integration with AI/LLM services for classification

### Current Data Flow
```
Frontend → Nginx → Document Service (CRUD operations)
Frontend → Nginx → S3 Service (file uploads)
```

## Proposed Orchestrator Architecture

### New Service: Prediction Service (Port 5006)

#### Core Functionality
1. **Confidence Threshold Routing**: First calls AI service, evaluates confidence, calls LLM if needed
2. **Response Aggregation**: Combines responses from both services intelligently  
3. **Fallback Handling**: Manages service failures gracefully
4. **Performance Optimization**: Caches results and manages timeouts

#### Service Flow
```
Frontend → Nginx → Prediction Service → AI Service (first attempt)
                                     → LLM Service (if confidence < threshold)
                                     → Aggregated Response → Frontend
```

## Prediction Service Design

### 1. Configuration Parameters
```python
# Default confidence thresholds (overridable from frontend)
DEFAULT_PRIMARY_CONFIDENCE_THRESHOLD = 0.90    
DEFAULT_SECONDARY_CONFIDENCE_THRESHOLD = 0.85
DEFAULT_TERTIARY_CONFIDENCE_THRESHOLD = 0.80

# Service URLs (internal Docker network)
AI_SERVICE_URL = "http://ai-service:5004"
LLM_SERVICE_URL = "http://llm-service:5005"

# Timeouts
AI_SERVICE_TIMEOUT = 30  # seconds
LLM_SERVICE_TIMEOUT = 120  # seconds
```

### 2. API Endpoints

#### `/predict` (POST)
**Request Format:**
```json
{
  "text": "document content...",
  "predict_levels": ["primary", "secondary", "tertiary"],
  "confidence_thresholds": {  // frontend can override defaults
    "primary": 0.90,
    "secondary": 0.85,
    "tertiary": 0.80
  }
}
```

**Response Format:**
```json
{
  "prediction": {
    "primary": {
      "pred": "News",
      "confidence": 0.98,
      "reasoning": "...",
      "source": "ai",  // "ai" or "llm" - which service provided this prediction
      "ai_prediction": {...},  // original AI prediction if available
      "llm_prediction": {...}  // LLM prediction if this level was processed by LLM
    },
    "secondary": {
      "pred": "Company",
      "confidence": 0.95,
      "reasoning": "...",
      "source": "llm",  // LLM was called because secondary was below threshold
      "ai_prediction": {...},
      "llm_prediction": {...}
    },
    "tertiary": {
      "pred": "Management_Change", 
      "confidence": 0.92,
      "reasoning": "...",
      "source": "llm",  // LLM was called because parent (secondary) was below threshold
      "ai_prediction": {...},
      "llm_prediction": {...}
    }
  },
  "elapsed_seconds": 6.2,
  "processed_text": "...",
  "service_calls": {
    "ai_service": { "called": true, "duration": 2.1, "success": true },
    "llm_service": { 
      "called": true, 
      "duration": 5.8, 
      "success": true,
      "levels_requested": ["secondary", "tertiary"]  // which levels LLM processed
    }
  },
  "confidence_analysis": {
    "triggered_llm": true,
    "trigger_level": "secondary",  // which level triggered LLM call
    "levels_below_threshold": ["secondary"]
  }
}
```

#### `/health` (GET)
Health check for orchestrator and downstream services

#### `/config` (GET)
Returns current configuration and thresholds

### 3. Decision Logic

#### Hierarchical Confidence Evaluation Strategy
1. **Call AI Service first** (faster, lower cost) for all requested levels
2. **Evaluate each prediction level** against its threshold in hierarchical order:
   - Check primary confidence against threshold
   - If primary < threshold → LLM processes primary, secondary, tertiary
   - If primary ≥ threshold, check secondary confidence against threshold
   - If secondary < threshold → LLM processes secondary, tertiary (keeping AI primary)
   - If secondary ≥ threshold, check tertiary confidence against threshold
   - If tertiary < threshold → LLM processes only tertiary (keeping AI primary + secondary)
3. **Make targeted LLM call** only for levels that need processing
4. **Aggregate responses** using AI predictions for above-threshold levels and LLM predictions for below-threshold levels

#### Response Aggregation Rules
1. **Use AI predictions** for levels that met confidence threshold
2. **Use LLM predictions** for levels that were below threshold (and their children)
3. **Maintain hierarchy**: If a parent level triggers LLM, all child levels use LLM predictions
4. **Full transparency**: Include both AI and LLM predictions in response for comparison
5. **Fallback Strategy**: If one service fails, use the other service's results

#### Example Scenarios

**Scenario 1: All levels above threshold**
- AI: primary=0.95, secondary=0.90, tertiary=0.85 
- Thresholds: 0.90, 0.85, 0.80
- Result: Use all AI predictions, no LLM call

**Scenario 2: Secondary below threshold**
- AI: primary=0.95, secondary=0.80, tertiary=0.85
- Thresholds: 0.90, 0.85, 0.80  
- Result: Keep AI primary (0.95), call LLM for secondary+tertiary

**Scenario 3: Primary below threshold**
- AI: primary=0.85, secondary=0.90, tertiary=0.85
- Thresholds: 0.90, 0.85, 0.80
- Result: Call LLM for all levels (primary+secondary+tertiary)

### 4. Service Implementation Structure

```python
# backend/prediction-service/
├── app.py                 # FastAPI main application
├── config.py              # Configuration management
├── models.py              # Pydantic request/response models
├── services/
│   ├── ai_client.py       # AI service client
│   ├── llm_client.py      # LLM service client
│   └── aggregator.py      # Response aggregation logic
├── utils/
│   ├── confidence.py      # Confidence evaluation logic
│   └── fallback.py        # Error handling and fallbacks
├── requirements.txt
├── Dockerfile
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### 5. Error Handling & Resilience

#### Service Failure Scenarios
1. **AI Service Down**: Call LLM directly, mark as fallback
2. **LLM Service Down**: Use AI predictions regardless of confidence
3. **Both Services Down**: Return 503 with appropriate error message
4. **Timeout Handling**: Configurable timeouts for each service
5. **Partial Failures**: Handle cases where one service returns partial results

#### Circuit Breaker Pattern
- Implement circuit breaker for each downstream service
- Open circuit after N consecutive failures
- Half-open state for gradual recovery testing

### 6. Integration Requirements

#### Nginx Configuration Update
Add new upstream and location block:
```nginx
upstream prediction_service { server prediction-service:5006; }

location ^~ /predict/ {
    proxy_pass http://prediction_service/;
    proxy_http_version 1.1;
    proxy_read_timeout 180s;  # Longer timeout for LLM calls
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    proxy_hide_header Access-Control-Allow-Origin;
    proxy_hide_header Access-Control-Allow-Credentials;
    proxy_hide_header Access-Control-Allow-Headers;
    proxy_hide_header Access-Control-Allow-Methods;

    add_header Access-Control-Allow-Origin $cors_origin always;
    add_header Vary "Origin" always;
    add_header Access-Control-Allow-Methods $cors_methods always;
    add_header Access-Control-Allow-Headers $cors_headers always;

    if ($request_method = OPTIONS) { return 204; }
}
```

#### Docker Compose Update
```yaml
prediction-service:
  build: ./prediction-service
  ports:
    - "5006:5006"
  depends_on:
    - ai-service
    - llm-service
  env_file:
    - .env
```

#### Frontend API Integration
Update `frontend/lib/api.ts`:
```typescript
async classifyDocument(
  text: string, 
  levels: string[], 
  confidenceThresholds?: { primary?: number; secondary?: number; tertiary?: number }
): Promise<ClassificationResponse> {
  return this.fetchWithErrorHandling<ClassificationResponse>(
    apiUrl("/predict/classify"),
    { 
      method: "POST", 
      body: JSON.stringify({ 
        text, 
        predict_levels: levels,
        confidence_thresholds: confidenceThresholds 
      }) 
    }
  );
}
```

## Requirements Summary

Based on the clarified requirements:

1. **Frontend-Configurable Thresholds**: Confidence thresholds are set by the frontend and passed in each request
2. **Hierarchical Processing**: If a parent level is below threshold, LLM processes that level and all children
3. **No Always-Both Mode**: LLM is only called when confidence thresholds are not met
4. **No Caching**: Results will be stored in the database, no service-level caching needed
5. **Hybrid Responses**: Final response uses AI for above-threshold levels, LLM for below-threshold levels
6. **Full Transparency**: Both AI and LLM predictions are included in the response for comparison

## Implementation Timeline

This design document serves as the foundation for implementing the orchestrator service. The next steps would involve:

1. Implementing the core orchestrator service
2. Adding comprehensive testing
3. Updating infrastructure configuration
4. Frontend integration
5. Monitoring and observability setup

## Benefits

1. **Cost Optimization**: Only call expensive LLM service when AI confidence is insufficient
2. **Hierarchical Intelligence**: Respects parent-child relationships in classification taxonomy
3. **Frontend Control**: Thresholds are configurable per request from the frontend
4. **Performance**: Fast AI service handles most classifications, LLM only for edge cases
5. **Transparency**: Full visibility into which service provided each prediction
6. **Accuracy**: Leverages LLM's superior performance for difficult classifications
7. **Resilience**: Fallback mechanisms ensure service availability