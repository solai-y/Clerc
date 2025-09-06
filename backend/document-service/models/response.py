from typing import Any, Optional
from datetime import datetime

class APIResponse:
    """Standardized API response format"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        response = {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        return response, status_code
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_code: Optional[str] = None) -> tuple:
        response = {
            "status": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if error_code:
            response["error_code"] = error_code
        return response, status_code
    
    @staticmethod
    def not_found(resource: str = "Resource") -> tuple:
        return APIResponse.error(f"{resource} not found", 404, "NOT_FOUND")
    
    @staticmethod
    def validation_error(message: str) -> tuple:
        return APIResponse.error(f"Validation error: {message}", 400, "VALIDATION_ERROR")
    
    @staticmethod
    def internal_error(message: str = "Internal server error") -> tuple:
        return APIResponse.error(message, 500, "INTERNAL_ERROR")