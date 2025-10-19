"""
FastAPI application for LLM-based document classification service
"""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import PredictionRequest, FullResponse
from prediction_service import PredictionService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global prediction service instance
prediction_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global prediction_service
    
    # Startup
    logger.info("Starting LLM Classification Service...")
    try:
        prediction_service = PredictionService()
        logger.info("Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down LLM Classification Service...")

# Create FastAPI app
app = FastAPI(
    title="LLM Document Classification Service",
    description="Claude Sonnet 4 powered document classification with hierarchical taxonomy",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "LLM Document Classification",
        "status": "healthy",
        "model": Config.CLAUDE_MODEL_ID,
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "llm-classification",
        "model": Config.CLAUDE_MODEL_ID,
        "aws_region": Config.AWS_REGION
    }

@app.post("/predict", response_model=FullResponse, response_model_exclude_none=True)
async def predict_document(request: PredictionRequest) -> FullResponse:
    """
    Classify document using Claude Sonnet 4
    
    Args:
        request: Prediction request with text, predict levels, and context
        
    Returns:
        Classification results with timing and confidence scores
        
    Raises:
        HTTPException: If classification fails after retries
    """
    global prediction_service
    
    if prediction_service is None:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized"
        )
    
    try:
        logger.info(f"Received prediction request for levels: {request.predict}")
        logger.info(f"Context provided: {request.context}")
        logger.info(f"Text length: {len(request.text)} characters")
        
        # Validate request
        if not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text cannot be empty"
            )
        
        if not request.predict:
            raise HTTPException(
                status_code=400,
                detail="Must specify at least one prediction level"
            )
        
        valid_levels = {"primary", "secondary", "tertiary"}
        for level in request.predict:
            if level not in valid_levels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid prediction level: {level}. Must be one of: {valid_levels}"
                )
        
        # Make prediction
        result = prediction_service.predict(
            text=request.text,
            predict_levels=request.predict,
            context=request.context
        )
        
        logger.info(f"Prediction completed in {result['elapsed_seconds']:.2f}s")
        
        return FullResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5005,
        reload=True,
        log_level="info"
    )