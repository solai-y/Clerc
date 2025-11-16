import os
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import custom modules
from models.response import APIResponse
from routes.documents import documents_router
from routes.metrics import metrics_router
from services.database import DatabaseService

# ---------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Initialize FastAPI app
# ---------------------------------------------------------------------
app = FastAPI(
    title="document-service",
    description="Document CRUD operations and metrics",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router, prefix="/documents")
app.include_router(metrics_router, prefix="/metrics")

# Initialize database service for health checks
try:
    db_service = DatabaseService()
    logger.info("Document service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize document service: {str(e)}")
    db_service = None

# ---------------------------------------------------------------------
# Pydantic models for OpenAPI schema (no Dict[str, Any] = no additionalProp*)
# ---------------------------------------------------------------------
class HealthStatus(BaseModel):
    service: str = Field(..., example="document-service")
    version: str = Field(..., example="1.0.0")
    timestamp: str = Field(..., example="2025-01-01T12:00:00Z")
    database_connected: bool = Field(..., example=True)
    error: Optional[str] = Field(None, example=None)

class HealthEnvelope(BaseModel):
    status: str = Field(..., example="success")
    message: str = Field(..., example="Document service is healthy")
    data: HealthStatus

class RouteInfo(BaseModel):
    path: str = Field(..., example="/documents")
    name: str = Field(..., example="get_documents")
    methods: List[str] = Field(default_factory=lambda: ["GET"], example=["GET"])

class RoutesEnvelope(BaseModel):
    routes: List[RouteInfo] = Field(
        ...,
        example={
            "routes": [
                {"path": "/documents", "name": "get_documents", "methods": ["GET"]},
                {"path": "/health", "name": "health_check", "methods": ["GET"]},
            ]
        },
    )

class E2EData(BaseModel):
    service: str = Field(..., example="document-service")

class E2EEnvelope(BaseModel):
    status: str = Field(..., example="success")
    message: str = Field(..., example="Document service is reachable")
    data: E2EData

class RootData(BaseModel):
    service: str = Field(..., example="document-service")
    version: str = Field(..., example="1.0.0")
    endpoints: List[str] = Field(
        ...,
        example=[
            "GET /health - Health check",
            "GET /e2e - End-to-end test",
            "GET /documents - Get all documents",
            "GET /documents/<id> - Get document by ID",
            "POST /documents - Create new document",
            "PUT /documents/<id> - Update document",
            "DELETE /documents/<id> - Delete document",
            "PATCH /documents/<id>/status - Update document status",
            "POST /documents/processed - Create processed document entry",
            "PATCH /documents/<id>/tags - Update document tags",
            "GET /documents/unprocessed - Get unprocessed documents",
            "GET /metrics/top-tag-accuracy - Get top-tag accuracy metrics",
        ],
    )

class RootEnvelope(BaseModel):
    status: str = Field(..., example="success")
    message: str = Field(..., example="Document service API")
    data: RootData

# ---------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and responses"""
    logger.info(f"{request.method} {request.url.path} - {request.client.host}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} - {request.method} {request.url.path}")
    return response

# ---------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = exc.errors()
    if errors:
        error = errors[0]
        field = error.get("loc", [""])[-1] if error.get("loc") else "field"
        error_type = error.get("type", "")
        if error_type == "missing":
            message = f"{field} field is required"
        elif error_type == "string_type":
            message = f"{field} must be a string"
        elif error_type == "list_type":
            message = f"{field} must be an array"
        elif "validation" in error_type:
            message = f"Validation failed for {field}"
        else:
            msg = error.get("msg", "").lower()
            if "list" in msg or "array" in msg:
                message = f"{field} must be an array"
            else:
                message = "Validation failed"
    else:
        message = "Validation failed"
    return APIResponse.error(message, 400, "VALIDATION_ERROR")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return APIResponse.not_found("Endpoint")

@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    """Handle 405 errors"""
    return APIResponse.error("Method not allowed", 405, "METHOD_NOT_ALLOWED")

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}")
    return APIResponse.internal_error()

# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthEnvelope,
    summary="Health Check",
    description="Check if the document service and database are operational",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Document service is healthy",
                        "data": {
                            "service": "document-service",
                            "version": "1.0.0",
                            "timestamp": "2025-01-01T12:00:00Z",
                            "database_connected": True,
                            "error": None,
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service Unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Document service is unhealthy",
                        "code": "SERVICE_UNHEALTHY",
                    }
                }
            },
        },
    },
)
async def health_check():
    health_status = {
        "service": "document-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }

    if db_service:
        db_connected, db_error = db_service.test_connection()
        health_status["database_connected"] = db_connected
        if db_error:
            health_status["error"] = db_error
    else:
        health_status["database_connected"] = False
        health_status["error"] = "Database service not initialized"

    if health_status["database_connected"]:
        return APIResponse.success(health_status, "Document service is healthy")
    else:
        return APIResponse.error("Document service is unhealthy", 503, "SERVICE_UNHEALTHY")


@app.get(
    "/debug/routes",
    response_model=RoutesEnvelope,
    summary="Debug Routes",
    description="Show all registered API routes for debugging purposes",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "routes": [
                            {"path": "/documents", "name": "get_documents", "methods": ["GET"]},
                            {"path": "/health", "name": "health_check", "methods": ["GET"]},
                        ]
                    }
                }
            }
        }
    },
)
async def debug_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else [],
        })
    return {"routes": routes}


@app.get(
    "/e2e",
    response_model=E2EEnvelope,
    summary="E2E Test",
    description="End-to-end test endpoint for document-service",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Document service is reachable",
                        "data": {"service": "document-service"},
                    }
                }
            }
        }
    },
)
async def e2e_test():
    logger.info("E2E test endpoint accessed")
    return APIResponse.success({"service": "document-service"}, "Document service is reachable")


@app.get(
    "/",
    response_model=RootEnvelope,
    summary="Root",
    description="Root endpoint providing a list of available routes",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Document service API",
                        "data": {
                            "service": "document-service",
                            "version": "1.0.0",
                            "endpoints": [
                                "GET /health - Health check",
                                "GET /e2e - End-to-end test",
                                "GET /documents - Get all documents",
                                "GET /documents/<id> - Get document by ID",
                                "POST /documents - Create new document",
                                "PUT /documents/<id> - Update document",
                                "DELETE /documents/<id> - Delete document",
                                "PATCH /documents/<id>/status - Update document status",
                                "POST /documents/processed - Create processed document entry",
                                "PATCH /documents/<id>/tags - Update document tags",
                                "GET /documents/unprocessed - Get unprocessed documents",
                                "GET /metrics/top-tag-accuracy - Get top-tag accuracy metrics",
                            ],
                        },
                    }
                }
            }
        }
    },
)
async def root():
    return APIResponse.success(
        {
            "service": "document-service",
            "version": "1.0.0",
            "endpoints": [
                "GET /health - Health check",
                "GET /e2e - End-to-end test",
                "GET /documents - Get all documents",
                "GET /documents/<id> - Get document by ID",
                "POST /documents - Create new document",
                "PUT /documents/<id> - Update document",
                "DELETE /documents/<id> - Delete document",
                "PATCH /documents/<id>/status - Update document status",
                "POST /documents/processed - Create processed document entry",
                "PATCH /documents/<id>/tags - Update document tags",
                "GET /documents/unprocessed - Get unprocessed documents",
                "GET /metrics/top-tag-accuracy - Get top-tag accuracy metrics",
            ],
        },
        "Document service API",
    )

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting document service on port 5002")
    uvicorn.run(app, host="0.0.0.0", port=5002)
