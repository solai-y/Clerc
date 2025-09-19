"""
Configuration settings for the prediction service
"""
import os
from typing import Dict

class Config:
    """Configuration class for prediction service"""
    
    # Service URLs (Docker internal network)
    AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:5004")
    LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:5005")
    
    # Default confidence thresholds (can be overridden by frontend)
    DEFAULT_PRIMARY_CONFIDENCE_THRESHOLD = float(os.getenv("DEFAULT_PRIMARY_THRESHOLD", "0.90"))
    DEFAULT_SECONDARY_CONFIDENCE_THRESHOLD = float(os.getenv("DEFAULT_SECONDARY_THRESHOLD", "0.85"))
    DEFAULT_TERTIARY_CONFIDENCE_THRESHOLD = float(os.getenv("DEFAULT_TERTIARY_THRESHOLD", "0.80"))
    
    # Service timeouts (seconds)
    AI_SERVICE_TIMEOUT = int(os.getenv("AI_SERVICE_TIMEOUT", "30"))
    LLM_SERVICE_TIMEOUT = int(os.getenv("LLM_SERVICE_TIMEOUT", "120"))
    
    # Circuit breaker settings
    MAX_FAILURES = int(os.getenv("MAX_FAILURES", "5"))
    FAILURE_TIMEOUT = int(os.getenv("FAILURE_TIMEOUT", "60"))  # seconds
    
    @classmethod
    def get_default_thresholds(cls) -> Dict[str, float]:
        """Get default confidence thresholds"""
        return {
            "primary": cls.DEFAULT_PRIMARY_CONFIDENCE_THRESHOLD,
            "secondary": cls.DEFAULT_SECONDARY_CONFIDENCE_THRESHOLD,
            "tertiary": cls.DEFAULT_TERTIARY_CONFIDENCE_THRESHOLD
        }