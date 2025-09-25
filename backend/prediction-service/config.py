"""
Configuration settings for the prediction service
"""
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for prediction service"""
    
    # Service URLs (Docker internal network)
    AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:5004")
    LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:5005")
    
    # Fallback confidence thresholds (used when database is unavailable)
    FALLBACK_PRIMARY_CONFIDENCE_THRESHOLD = float(os.getenv("FALLBACK_PRIMARY_THRESHOLD", "0.85"))
    FALLBACK_SECONDARY_CONFIDENCE_THRESHOLD = float(os.getenv("FALLBACK_SECONDARY_THRESHOLD", "0.80"))
    FALLBACK_TERTIARY_CONFIDENCE_THRESHOLD = float(os.getenv("FALLBACK_TERTIARY_THRESHOLD", "0.75"))
    
    # Service timeouts (seconds)
    AI_SERVICE_TIMEOUT = int(os.getenv("AI_SERVICE_TIMEOUT", "30"))
    LLM_SERVICE_TIMEOUT = int(os.getenv("LLM_SERVICE_TIMEOUT", "120"))
    
    # Circuit breaker settings
    MAX_FAILURES = int(os.getenv("MAX_FAILURES", "5"))
    FAILURE_TIMEOUT = int(os.getenv("FAILURE_TIMEOUT", "60"))  # seconds
    
    # Database service instance (will be set during app startup)
    _db_service: Optional['DatabaseService'] = None
    
    @classmethod
    def set_database_service(cls, db_service):
        """Set the database service instance"""
        cls._db_service = db_service
        logger.info("Database service configured for Config class")
    
    @classmethod
    def get_default_thresholds(cls) -> Dict[str, float]:
        """
        Get confidence thresholds - from database if available, otherwise fallback values
        """
        if cls._db_service:
            try:
                thresholds, error = cls._db_service.get_confidence_thresholds()
                if thresholds and not error:
                    logger.info(f"Using database thresholds: {thresholds}")
                    return thresholds
                else:
                    logger.warning(f"Database threshold retrieval failed: {error}, using fallback")
            except Exception as e:
                logger.warning(f"Exception getting database thresholds: {str(e)}, using fallback")
        
        # Use fallback values
        fallback_thresholds = {
            "primary": cls.FALLBACK_PRIMARY_CONFIDENCE_THRESHOLD,
            "secondary": cls.FALLBACK_SECONDARY_CONFIDENCE_THRESHOLD,
            "tertiary": cls.FALLBACK_TERTIARY_CONFIDENCE_THRESHOLD
        }
        logger.info(f"Using fallback thresholds: {fallback_thresholds}")
        return fallback_thresholds