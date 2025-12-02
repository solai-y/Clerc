# Company Service

FastAPI-based microservice for managing company data and metadata.

## Overview

The Company Service provides CRUD operations for company information including company profiles, industry classification, location data, and business metrics. It serves as the central service for all company-related data in the Clerc system.

## Key Features

- Company profile management (CRUD operations)
- Industry and location metadata
- Business metrics (revenue, employee count)
- RESTful API with automatic OpenAPI documentation

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `GET` | `/companies` | List all companies |
| `GET` | `/companies/{id}` | Get specific company by ID |
| `POST` | `/companies` | Create new company |
| `PUT` | `/companies/{id}` | Update existing company |
| `DELETE` | `/companies/{id}` | Delete company |

## Environment Variables

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Running Locally

**With Docker:**
```bash
cd backend
docker-compose up -d company-service
```

**Standalone:**
```bash
cd backend/company-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5001
```

## Service Configuration

- **Port:** 5001
- **Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)

## API Documentation

Once running, view interactive API docs at:
- Swagger UI: `http://localhost:5001/docs`
- ReDoc: `http://localhost:5001/redoc`

## Health Check

```bash
curl http://localhost:5001/health
```
