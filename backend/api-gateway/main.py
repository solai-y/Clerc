"""
Unified API Gateway - Aggregates documentation from all microservices
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import httpx

app = FastAPI(
    title="Clerc API Documentation",
    description="Unified API documentation for all Clerc microservices",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service endpoints (using internal Docker network ports)
SERVICES = {
    "company-service": "http://company-service:5001",
    "document-service": "http://document-service:5002",
    "s3-service": "http://s3-service:5003",
    "ai-service": "http://ai-service:5004",
    "llm-service": "http://llm-service:5005",
    "prediction-service": "http://prediction-service:5006",
    "text-extraction-service": "http://text-extraction-service:5008",
}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Clerc Unified API",
        version="1.0.0",
        description="Complete API documentation for all Clerc microservices",
        routes=app.routes,
    )

    # Fetch and merge OpenAPI specs from all services
    with httpx.Client(timeout=10.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = client.get(f"{service_url}/openapi.json")
                if response.status_code == 200:
                    service_spec = response.json()

                    # Merge paths with service prefix
                    if "paths" in service_spec:
                        for path, path_item in service_spec["paths"].items():
                            prefixed_path = f"/{service_name}{path}"

                            # Add service tag to all operations
                            for method, operation in path_item.items():
                                if isinstance(operation, dict) and "tags" not in operation:
                                    operation["tags"] = [service_name]
                                elif isinstance(operation, dict):
                                    operation["tags"].append(service_name)

                            openapi_schema["paths"][prefixed_path] = path_item

                    # Merge schemas
                    if "components" in service_spec and "schemas" in service_spec["components"]:
                        if "components" not in openapi_schema:
                            openapi_schema["components"] = {}
                        if "schemas" not in openapi_schema["components"]:
                            openapi_schema["components"]["schemas"] = {}

                        for schema_name, schema_def in service_spec["components"]["schemas"].items():
                            # Prefix schema names with service name to avoid conflicts
                            prefixed_name = f"{service_name}_{schema_name}"
                            openapi_schema["components"]["schemas"][prefixed_name] = schema_def

            except Exception as e:
                print(f"Failed to fetch OpenAPI spec from {service_name}: {e}")

    # Add tags for better organization
    openapi_schema["tags"] = [
        {"name": "ai-service", "description": "ML-based document classification"},
        {"name": "company-service", "description": "Company data management"},
        {"name": "document-service", "description": "Document CRUD operations"},
        {"name": "s3-service", "description": "File upload and storage"},
        {"name": "text-extraction-service", "description": "PDF text extraction"},
        {"name": "llm-service", "description": "LLM-based classification"},
        {"name": "prediction-service", "description": "Orchestration and aggregation"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
