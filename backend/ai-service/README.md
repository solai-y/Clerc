# AI Service

FastAPI-based microservice for hierarchical document classification using machine learning models.

## Overview

The AI Service provides ML-based document classification using scikit-learn models trained on hierarchical tag data. It supports both primary and best-fit tag prediction, model retraining, and validation endpoints. This service is the core of the automated document tagging system.

## Key Features

- Hierarchical tag prediction (Primary → Secondary → Tertiary)
- Two prediction models: primary tags and best-fit tags
- Automatic model retraining with dynamic sampling
- Tag validation against taxonomy
- Model performance metrics and monitoring
- Background training with progress tracking

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `POST` | `/predict` | Predict tags for document text |
| `POST` | `/retrain` | Trigger model retraining |
| `GET` | `/retrain/status` | Check retraining progress |
| `POST` | `/validate-tags` | Validate tag hierarchy against taxonomy |

## Prediction Request

**POST /predict**
```json
{
  "text": "Quarterly financial report showing 12% revenue growth..."
}
```

**Response:**
```json
{
  "primary_predictions": [
    {"tag": "Financial Documents", "confidence": 0.92},
    {"tag": "Earnings Reports", "confidence": 0.85}
  ],
  "best_predictions": [
    {
      "primary": "Financial Documents",
      "secondary": "Quarterly Reports",
      "tertiary": "Q1 Earnings",
      "confidence": 0.88
    }
  ]
}
```

## Environment Variables

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
RETRAINING_SERVICE_URL=http://retraining-service:5009
TAG_SERVICE_URL=http://tag-service:5007
```

## Running Locally

**With Docker:**
```bash
cd backend
docker-compose up -d ai-service
```

**Standalone:**
```bash
cd backend/ai-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5004
```

## Service Configuration

- **Port:** 5004
- **Framework:** FastAPI
- **ML Library:** scikit-learn
- **Model Storage:** `models_hier/` directory
- **Dependencies:** retraining-service, tag-service

## Model Retraining

Trigger retraining with:
```bash
curl -X POST "http://localhost:5004/retrain"
```

Check status:
```bash
curl "http://localhost:5004/retrain/status"
```

## Training Requirements

- Minimum 10 documents per tag for training
- Dynamic sampling for class balance
- Hierarchical validation during training

## API Documentation

Once running, view interactive API docs at:
- Swagger UI: `http://localhost:5004/docs`
- ReDoc: `http://localhost:5004/redoc`

## Health Check

```bash
curl http://localhost:5004/health
```
