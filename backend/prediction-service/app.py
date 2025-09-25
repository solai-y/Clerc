"""
FastAPI application for prediction service orchestrator
"""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import Config
from models import (
    PredictionRequest, FullPredictionResponse, HealthResponse, ConfigResponse,
    ServiceCalls, ServiceCallInfo, ConfidenceAnalysis, UpdateThresholdsRequest,
    ThresholdConfigResponse, ThresholdHistoryResponse, ThresholdHistoryItem,
    TextExtractionRequest, TextExtractionResponse
)
from services.ai_client import AIServiceClient
from services.llm_client import LLMServiceClient
from services.aggregator import ResponseAggregator
from services.database import DatabaseService
from services.text_extraction import TextExtractionService
from utils.confidence import ConfidenceEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service clients
ai_client = None
llm_client = None
db_service = None
text_extraction_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ai_client, llm_client, db_service, text_extraction_service
    
    # Startup
    logger.info("Starting Prediction Service Orchestrator...")
    try:
        # Initialize database service first
        db_service = DatabaseService()
        Config.set_database_service(db_service)
        logger.info("Database service initialized successfully")
        
        # Initialize other service clients
        ai_client = AIServiceClient()
        llm_client = LLMServiceClient()
        text_extraction_service = TextExtractionService()
        logger.info("All service clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service clients: {str(e)}")
        # Don't raise - allow service to start with fallback configuration
        logger.warning("Service will start with fallback configuration")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Prediction Service Orchestrator...")
    if text_extraction_service:
        await text_extraction_service.close()

# Create FastAPI app
app = FastAPI(
    title="Document Classification Prediction Service",
    description="Orchestrator service for intelligent routing between AI and LLM services",
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
    """Root endpoint"""
    return {
        "service": "Document Classification Prediction Service",
        "status": "healthy",
        "version": "1.0.0",
        "description": "Orchestrator for AI and LLM classification services"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check including downstream services"""
    global ai_client, llm_client
    
    if ai_client is None or llm_client is None:
        raise HTTPException(status_code=503, detail="Service clients not initialized")
    
    # Check downstream services
    ai_health = await ai_client.health_check()
    llm_health = await llm_client.health_check()
    
    downstream_services = {
        "ai_service": ai_health["status"],
        "llm_service": llm_health["status"]
    }
    
    overall_status = "healthy" if all(
        status == "healthy" for status in downstream_services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=time.time(),
        downstream_services=downstream_services
    )

@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    return ConfigResponse(
        default_thresholds=Config.get_default_thresholds(),
        service_urls={
            "ai_service": Config.AI_SERVICE_URL,
            "llm_service": Config.LLM_SERVICE_URL
        },
        timeouts={
            "ai_service": Config.AI_SERVICE_TIMEOUT,
            "llm_service": Config.LLM_SERVICE_TIMEOUT
        }
    )

@app.post("/classify", response_model=FullPredictionResponse)
async def classify_document(request: PredictionRequest) -> FullPredictionResponse:
    """
    Main classification endpoint that orchestrates between AI and LLM services
    
    Args:
        request: Classification request with text, levels, and optional thresholds
        
    Returns:
        Complete classification response with service call information
        
    Raises:
        HTTPException: If classification fails
    """
    global ai_client, llm_client
    
    if ai_client is None or llm_client is None:
        raise HTTPException(status_code=503, detail="Service clients not initialized")
    
    start_time = time.time()
    
    try:
        logger.info(f"Received classification request for levels: {request.predict_levels}")
        
        # Validate request
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if not request.predict_levels:
            raise HTTPException(status_code=400, detail="Must specify at least one prediction level")
        
        valid_levels = {"primary", "secondary", "tertiary"}
        for level in request.predict_levels:
            if level not in valid_levels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid prediction level: {level}. Must be one of: {valid_levels}"
                )
        
        # Get confidence thresholds (use request overrides or defaults)
        thresholds = Config.get_default_thresholds()
        if request.confidence_thresholds:
            if request.confidence_thresholds.primary is not None:
                thresholds["primary"] = request.confidence_thresholds.primary
            if request.confidence_thresholds.secondary is not None:
                thresholds["secondary"] = request.confidence_thresholds.secondary
            if request.confidence_thresholds.tertiary is not None:
                thresholds["tertiary"] = request.confidence_thresholds.tertiary
        
        logger.info(f"Using confidence thresholds: {thresholds}")
        
        # Step 1: Call AI service first
        logger.info("Step 1: Calling AI service...")
        ai_predictions = await ai_client.predict(request.text, request.predict_levels)
        ai_success = True
        ai_duration = ai_predictions.get("duration", 0.0)
        
        # Step 2: Evaluate confidence thresholds
        logger.info("Step 2: Evaluating confidence thresholds...")
        needs_llm, trigger_level, levels_below_threshold = ConfidenceEvaluator.evaluate_thresholds(
            ai_predictions, thresholds, request.predict_levels
        )
        
        # Initialize LLM variables
        llm_predictions = None
        llm_success = False
        llm_duration = 0.0
        llm_levels = []
        
        # Step 3: Call LLM service if needed
        if needs_llm:
            logger.info(f"Step 3: Calling LLM service for levels: {levels_below_threshold}")
            
            try:
                # Determine which levels LLM should process
                llm_levels = ConfidenceEvaluator.determine_llm_levels(trigger_level, request.predict_levels)
                
                # Build context from AI predictions that we're keeping
                context = ConfidenceEvaluator.build_llm_context(ai_predictions, llm_levels)
                
                # Call LLM service
                llm_predictions = await llm_client.predict(request.text, llm_levels, context)
                llm_success = True
                llm_duration = llm_predictions.get("duration", 0.0)
                
            except Exception as e:
                logger.error(f"LLM service call failed: {str(e)}")
                # Continue with AI predictions only
                llm_success = False
        else:
            logger.info("Step 3: Skipping LLM service (all confidence levels met)")
        
        # Step 4: Aggregate responses
        logger.info("Step 4: Aggregating responses...")
        final_predictions = ResponseAggregator.aggregate_predictions(
            ai_predictions, llm_predictions, llm_levels, request.predict_levels
        )
        
        # Calculate total elapsed time
        total_elapsed = ResponseAggregator.merge_service_timing(ai_predictions, llm_predictions)
        
        # Build service call information
        service_calls = ServiceCalls(
            ai_service=ServiceCallInfo(
                called=True,
                duration=ai_duration,
                success=ai_success,
                levels_requested=request.predict_levels
            ),
            llm_service=ServiceCallInfo(
                called=needs_llm,
                duration=llm_duration,
                success=llm_success,
                levels_requested=llm_levels if needs_llm else None
            )
        )
        
        # Build confidence analysis
        confidence_analysis = ConfidenceAnalysis(
            triggered_llm=needs_llm,
            trigger_level=trigger_level,
            levels_below_threshold=levels_below_threshold
        )
        
        # Build final response
        response = FullPredictionResponse(
            prediction=final_predictions,
            elapsed_seconds=time.time() - start_time,
            processed_text=ai_predictions.get("processed_text", request.text),
            service_calls=service_calls,
            confidence_analysis=confidence_analysis
        )
        
        logger.info(f"Classification completed in {response.elapsed_seconds:.2f}s")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        logger.error(f"Classification failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )

# Text Extraction Endpoints

@app.post("/extract/pdf")
async def extract_pdf_text(request: TextExtractionRequest):
    """
    Extract text from PDF at given URL
    
    Args:
        request: Text extraction request with PDF URL
        
    Returns:
        APIResponse with extracted text and metadata
        
    Raises:
        HTTPException: If text extraction fails
    """
    global text_extraction_service
    
    if not text_extraction_service:
        raise HTTPException(
            status_code=503,
            detail="Text extraction service not available"
        )
    
    try:
        logger.info(f"Extracting text from PDF: {request.pdf_url}")
        
        # Extract text from PDF
        extracted_text = await text_extraction_service.extract_text_from_url(request.pdf_url)
        
        # Count pages (approximate from page markers)
        page_count = extracted_text.count("[Page ") if "[Page " in extracted_text else 1
        character_count = len(extracted_text)
        
        logger.info(f"Successfully extracted {character_count} characters from {page_count} pages")
        
        return {
            "status": "success",
            "message": f"Successfully extracted text from PDF ({page_count} pages, {character_count} characters)",
            "data": {
                "text": extracted_text,
                "page_count": page_count,
                "character_count": character_count
            },
            "timestamp": str(time.time())
        }
        
    except Exception as e:
        logger.error(f"PDF text extraction failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"PDF text extraction failed: {str(e)}"
        )

# Configuration Management Endpoints

@app.get("/config/thresholds")
async def get_confidence_thresholds():
    """Get current confidence thresholds"""
    global db_service
    
    if not db_service:
        # Return fallback thresholds
        fallback_thresholds = Config.get_default_thresholds()
        return {
            "status": "success",
            "message": "Retrieved confidence thresholds (fallback)",
            "data": {
                "primary": fallback_thresholds["primary"],
                "secondary": fallback_thresholds["secondary"],
                "tertiary": fallback_thresholds["tertiary"],
                "updated_at": None,
                "updated_by": "fallback"
            },
            "timestamp": str(time.time())
        }
    
    try:
        thresholds, error = db_service.get_confidence_thresholds()
        if error:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve thresholds: {error}")
        
        return {
            "status": "success",
            "message": "Retrieved confidence thresholds from database",
            "data": {
                "primary": thresholds["primary"],
                "secondary": thresholds["secondary"],
                "tertiary": thresholds["tertiary"],
                "updated_at": None,  # Could be enhanced to return actual update time
                "updated_by": None   # Could be enhanced to return actual updater
            },
            "timestamp": str(time.time())
        }
    except Exception as e:
        logger.error(f"Error getting thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve thresholds: {str(e)}")

@app.put("/config/thresholds")
async def update_confidence_thresholds(request: UpdateThresholdsRequest):
    """Update confidence thresholds"""
    global db_service
    
    if not db_service:
        raise HTTPException(
            status_code=503, 
            detail="Database service not available. Cannot update thresholds."
        )
    
    try:
        # Validate that at least one threshold is provided
        if request.primary is None and request.secondary is None and request.tertiary is None:
            raise HTTPException(
                status_code=400,
                detail="At least one threshold must be provided"
            )
        
        updated_thresholds, error = db_service.update_confidence_thresholds(
            primary=request.primary,
            secondary=request.secondary,
            tertiary=request.tertiary,
            updated_by=request.updated_by
        )
        
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        logger.info(f"Confidence thresholds updated: {updated_thresholds}")
        return {
            "status": "success",
            "message": "Confidence thresholds updated successfully",
            "data": {
                "primary": updated_thresholds["primary"],
                "secondary": updated_thresholds["secondary"],
                "tertiary": updated_thresholds["tertiary"],
                "updated_at": None,  # Could be enhanced
                "updated_by": request.updated_by
            },
            "timestamp": str(time.time())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update thresholds: {str(e)}")

@app.get("/config/thresholds/history", response_model=ThresholdHistoryResponse)
async def get_threshold_history(limit: int = 10):
    """Get threshold change history"""
    global db_service
    
    if not db_service:
        raise HTTPException(
            status_code=503,
            detail="Database service not available. Cannot retrieve history."
        )
    
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        
        history, error = db_service.get_threshold_history(limit=limit)
        if error:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {error}")
        
        history_items = [
            ThresholdHistoryItem(
                primary_threshold=item["primary_threshold"],
                secondary_threshold=item["secondary_threshold"],
                tertiary_threshold=item["tertiary_threshold"],
                updated_at=item["updated_at"],
                updated_by=item["updated_by"]
            )
            for item in history
        ]
        
        return ThresholdHistoryResponse(
            history=history_items,
            total_count=len(history_items)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting threshold history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

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
        "app:app",
        host="0.0.0.0",
        port=5006,
        reload=True,
        log_level="info"
    )