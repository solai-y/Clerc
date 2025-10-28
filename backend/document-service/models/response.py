from typing import Any, Optional
from datetime import datetime
from fastapi.responses import JSONResponse

class APIResponse:
    """Standardized API response format for FastAPI"""

    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> JSONResponse:
        response = {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(status_code=status_code, content=response)

    @staticmethod
    def error(message: str, status_code: int = 400, error_code: Optional[str] = None) -> JSONResponse:
        response = {
            "status": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if error_code:
            response["error_code"] = error_code
        return JSONResponse(status_code=status_code, content=response)

    @staticmethod
    def not_found(resource: str = "Resource") -> JSONResponse:
        return APIResponse.error(f"{resource} not found", 404, "NOT_FOUND")

    @staticmethod
    def validation_error(message: str) -> JSONResponse:
        return APIResponse.error(f"Validation error: {message}", 400, "VALIDATION_ERROR")

    @staticmethod
    def internal_error(message: str = "Internal server error") -> JSONResponse:
        return APIResponse.error(message, 500, "INTERNAL_ERROR")