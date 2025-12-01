# API Gateway

Unified API gateway aggregating documentation and routing for all Clerc microservices.

## Overview

The API Gateway serves as the single entry point for accessing all Clerc microservices. It provides unified OpenAPI documentation, request routing, and serves as a central documentation hub for developers working with the Clerc API.

## Key Features

- Unified OpenAPI/Swagger documentation for all services
- Request routing to microservices
- Component namespace management
- CORS configuration
- Centralized API versioning

## Aggregated Services

The gateway aggregates the following microservices:

1. **company-service** (port 5001) - Company data management
2. **document-service** (port 5002) - Document metadata CRUD
3. **s3-service** (port 5003) - File upload/storage
4. **ai-service** (port 5004) - ML-based tag prediction
5. **llm-service** (port 5005) - LLM-based classification
6. **prediction-service** (port 5006) - Prediction orchestration
7. **text-extraction-service** (port 5008) - PDF text extraction
8. **retraining-service** (port 5009) - Training data management

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/docs` | Unified Swagger UI documentation |
| `GET` | `/redoc` | Unified ReDoc documentation |
| `GET` | `/openapi.json` | Combined OpenAPI specification |

All service endpoints are accessible through the gateway with their original paths.

## Environment Variables

No specific environment variables required. The gateway uses internal Docker network for service communication.

## Running Locally

**With Docker:**
```bash
cd backend
docker-compose up -d api-gateway
```

**Standalone:**
```bash
cd backend/api-gateway
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Service Configuration

- **Port:** 8000
- **Framework:** FastAPI
- **Dependencies:** All microservices must be running

## Accessing Documentation

Once running, access the unified API documentation at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

The documentation includes all endpoints from all microservices in a single, browsable interface.

## Architecture

The gateway fetches OpenAPI specifications from each microservice at startup, merges them with namespace prefixing to avoid conflicts, and serves a unified documentation interface. All requests are proxied to the appropriate backend service.

## Service Discovery

Services are accessed via Docker internal networking:
```python
SERVICES = {
    "company-service": "http://company-service:5001",
    "document-service": "http://document-service:5002",
    # ... etc
}
```

## Development

For local development, ensure all microservices are running:
```bash
docker-compose up -d
```

Then access the gateway at `http://localhost:8000/docs` to explore all available endpoints.
