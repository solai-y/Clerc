import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

# Import custom modules
from models.response import APIResponse
from routes.documents import documents_router
from services.database import DatabaseService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router, prefix='/documents')

# Initialize database service for health checks
try:
    db_service = DatabaseService()
    logger.info("Document service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize document service: {str(e)}")
    db_service = None

# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and responses"""
    logger.info(f"{request.method} {request.url.path} - {request.client.host}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} - {request.method} {request.url.path}")
    return response

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = exc.errors()
    if errors:
        # Create a more descriptive error message based on the validation error
        error = errors[0]
        field = error.get('loc', [''])[-1] if error.get('loc') else 'field'
        error_type = error.get('type', '')
        
        if error_type == 'missing':
            message = f"{field} field is required"
        elif error_type == 'string_type':
            message = f"{field} must be a string"
        elif error_type == 'list_type':
            message = f"{field} must be an array"
        elif 'validation' in error_type:
            message = f"Validation failed for {field}"
        else:
            # Look at the actual error message for more context
            error_msg = error.get('msg', '').lower()
            if 'list' in error_msg or 'array' in error_msg:
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

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    health_status = {
        "service": "document-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Test database connection
    if db_service:
        db_connected, db_error = db_service.test_connection()
        health_status["database_connected"] = db_connected
        if db_error:
            health_status["error"] = db_error
    else:
        health_status["database_connected"] = False
        health_status["error"] = "Database service not initialized"

    # Determine overall health
    if health_status["database_connected"]:
        return APIResponse.success(health_status, "Document service is healthy")
    else:
        return APIResponse.error("Document service is unhealthy", 503, "SERVICE_UNHEALTHY")

@app.get('/debug/routes')
async def debug_routes():
    """Debug endpoint to show all registered routes"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, 'methods') else []
        })
    return {"routes": routes}

@app.get('/e2e')
async def e2e_test():
    """End-to-end test endpoint"""
    logger.info("E2E test endpoint accessed")
    return APIResponse.success({"service": "document-service"}, "Document service is reachable")

@app.get('/')
async def root():
    """Root endpoint"""
    return APIResponse.success({
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
            "GET /documents/unprocessed - Get unprocessed documents"
        ]
    }, "Document service API")

if __name__ == '__main__':
    import uvicorn
    logger.info("Starting document service on port 5002")
    uvicorn.run(app, host='0.0.0.0', port=5002)