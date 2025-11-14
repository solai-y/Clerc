"""
Unified API Gateway - Aggregates documentation from all microservices
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import httpx
from copy import deepcopy
import re  # NEW: used in ref safety pass

app = FastAPI(
    title="Clerc API Documentation",
    description="Unified API documentation for all Clerc microservices",
    version="1.0.0"
)

# CORS (unchanged)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service endpoints (unchanged: internal Docker network ports)
SERVICES = {
    "company-service": "http://company-service:5001",
    "document-service": "http://document-service:5002",
    "s3-service": "http://s3-service:5003",
    "ai-service": "http://ai-service:5004",
    "llm-service": "http://llm-service:5005",
    "prediction-service": "http://prediction-service:5006",
    "text-extraction-service": "http://text-extraction-service:5008",
    "retraining-service": "http://retraining-service:5009",
}

# ---- helper to prefix components and fix $ref (kept, with no behavior change) ----
def _prefix_and_rewrite_refs(service_spec: dict, service_name: str) -> dict:
    """
    Prefix all component names with <service_name>_ and rewrite all $ref values
    to point at the newly prefixed names. Works for all component blocks.
    """
    spec = deepcopy(service_spec)
    spec.setdefault("components", {})

    # All component blocks we might need to merge
    comp_keys = [
        "schemas", "parameters", "responses", "requestBodies",
        "headers", "examples", "links", "callbacks", "securitySchemes"
    ]

    # Build a mapping from old ref -> new ref after renaming
    ref_map = {}

    for key in comp_keys:
        if key not in spec["components"]:
            continue
        new_block = {}
        for name, val in spec["components"][key].items():
            new_name = f"{service_name}_{name}"
            ref_map[f"#/components/{key}/{name}"] = f"#/components/{key}/{new_name}"
            new_block[new_name] = val
        spec["components"][key] = new_block

    # Walk the whole document and rewrite $ref values
    def _walk(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if k == "$ref" and isinstance(v, str) and v in ref_map:
                    node[k] = ref_map[v]
                else:
                    _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(spec)
    return spec
# -------------------------------------------------------------------------------


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
                if response.status_code != 200:
                    continue

                # Prefix components and fix $refs before merging
                service_spec = _prefix_and_rewrite_refs(response.json(), service_name)

                # -------- Merge paths with service prefix (kept) --------
                openapi_schema.setdefault("paths", {})
                for path, path_item in service_spec.get("paths", {}).items():
                    prefixed_path = f"/{service_name}{path}"

                    # Add service tag to all operations (preserve + ensure presence)
                    for method, operation in path_item.items():
                        if isinstance(operation, dict):
                            operation.setdefault("tags", [])
                            if service_name not in operation["tags"]:
                                operation["tags"].append(service_name)

                    openapi_schema["paths"][prefixed_path] = path_item

                # -------- Merge ALL component blocks, defensively --------
                src_components = service_spec.get("components", {}) or {}
                dst_components = openapi_schema.setdefault("components", {})
                for k in [
                    "schemas", "parameters", "responses", "requestBodies",
                    "headers", "examples", "links", "callbacks", "securitySchemes"
                ]:
                    dst_components.setdefault(k, {})

                merged_counts = {}
                for key, block in src_components.items():
                    if not isinstance(block, dict):
                        continue
                    before = len(dst_components.get(key, {}))
                    # names are already prefixed -> safe to update
                    dst_components[key].update(block)
                    after = len(dst_components.get(key, {}))
                    merged_counts[key] = after - before

                # Optional: log summary to stdout for quick diagnosis
                print(f"[gateway] merged components from {service_name}: " +
                      ", ".join(f"{k}+{v}" for k, v in merged_counts.items() if v))

                # -------- Safety net: ensure all $ref in these paths are resolvable --------
                def _ensure_refs_resolvable(paths_node, components_node, service_components):
                    # Build a set of existing component refs
                    existing = set()
                    for comp_key, comp_block in components_node.items():
                        if isinstance(comp_block, dict):
                            for name in comp_block.keys():
                                existing.add(f"#/components/{comp_key}/{name}")

                    def _fix_schema(node):
                        if not isinstance(node, dict):
                            return
                        if "$ref" in node:
                            ref = node["$ref"]
                            if ref not in existing:
                                # Try to inject the missing component from the service spec (already prefixed)
                                m = re.match(r"^#/components/([^/]+)/(.+)$", ref)
                                if m:
                                    comp_key, comp_name = m.group(1), m.group(2)
                                    src_block = service_components.get(comp_key, {})
                                    if isinstance(src_block, dict) and comp_name in src_block:
                                        components_node[comp_key][comp_name] = src_block[comp_name]
                                        existing.add(ref)
                                        print(f"[gateway] injected missing component {ref}")
                                # If still missing, inline a permissive object so Swagger doesn't show 'string'
                                if ref not in existing:
                                    node.pop("$ref", None)
                                    node["type"] = "object"
                                    node["additionalProperties"] = True
                                    print(f"[gateway][warn] inlined unresolved $ref {ref}")
                            return
                        # Recurse
                        for v in node.values():
                            if isinstance(v, dict):
                                _fix_schema(v)
                            elif isinstance(v, list):
                                for it in v:
                                    if isinstance(it, dict):
                                        _fix_schema(it)

                    _fix_schema(paths_node)

                # Run the safety pass only for paths from this service
                for path in service_spec.get("paths", {}):
                    prefixed_path = f"/{service_name}{path}"
                    pnode = openapi_schema["paths"].get(prefixed_path)
                    if pnode:
                        _ensure_refs_resolvable(pnode, openapi_schema["components"], src_components)

            except Exception as e:
                print(f"Failed to fetch OpenAPI spec from {service_name}: {e}")

    # Tags for better organization (kept as-is, you can extend freely)
    openapi_schema["tags"] = [
        {"name": "ai-service", "description": "ML-based document classification"},
        {"name": "company-service", "description": "Company data management"},
        {"name": "document-service", "description": "Document CRUD operations"},
        {"name": "s3-service", "description": "File upload and storage"},
        {"name": "text-extraction-service", "description": "PDF text extraction"},
        {"name": "llm-service", "description": "LLM-based classification"},
        {"name": "prediction-service", "description": "Orchestration and aggregation"},
        {"name": "retraining-service", "description": "Training data & pipelines"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# keep your assignment
app.openapi = custom_openapi

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
