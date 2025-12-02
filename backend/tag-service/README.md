# Tag Service

FastAPI-based microservice managing the 3-level hierarchical tag taxonomy (Primary → Secondary → Tertiary).

## Overview

The Tag Service provides comprehensive management of the hierarchical tag system used for document classification in Clerc. It maintains a 3-tier taxonomy structure with parent-child relationships and validation.

## Key Features

- 3-level tag hierarchy (Primary → Secondary → Tertiary)
- Parent-child relationship validation
- Tag CRUD operations
- Hierarchical tag tree retrieval
- Tag validation and normalization

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `GET` | `/tags` | Get complete tag hierarchy tree |
| `GET` | `/tags/flat` | Get flat list of all tags |
| `GET` | `/tags/{id}` | Get specific tag by ID |
| `POST` | `/tags` | Create new tag |
| `PUT` | `/tags/{id}` | Update existing tag |
| `DELETE` | `/tags/{id}` | Delete tag |
| `GET` | `/tags/validate-hierarchy` | Validate tag hierarchy relationships |

## Tag Hierarchy Structure

```
Primary Tag (Level 1)
  └── Secondary Tag (Level 2)
       └── Tertiary Tag (Level 3)
```

**Example:**
```
Financial Documents
  └── Annual Reports
       └── Q4 Earnings
```

## Environment Variables

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Running Locally

**With Docker:**
```bash
cd backend
docker-compose up -d tag-service
```

**Standalone:**
```bash
cd backend/tag-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5007
```

## Service Configuration

- **Port:** 5007
- **Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)
- **Health Check:** Included in docker-compose.yml

## API Documentation

Once running, view interactive API docs at:
- Swagger UI: `http://localhost:5007/docs`
- ReDoc: `http://localhost:5007/redoc`

## Health Check

```bash
curl http://localhost:5007/health
# or
curl http://localhost:5007/tags
```
