"""
FastAPI application for LLM-based document classification service
"""
import logging
import time
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from models import PredictionRequest, FullResponse
from prediction_service import PredictionService
from config import Config

# Add parent directory to path to import shared utilities
parent_dir = Path(__file__).parent.parent
if parent_dir not in [Path(p) for p in map(Path, sys.path)]:
    sys.path.insert(0, str(parent_dir))
from shared_utils.text_preprocessing import clean_text  # noqa: E402

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# OpenAPI helper models for clean docs
# ------------------------------------------------------------------------------
class RootHealthModel(BaseModel):
    service: str = Field(..., example="LLM Document Classification")
    status: str = Field(..., example="healthy")
    model: str = Field(..., example="claude-3-5-sonnet-20241022")
    version: str = Field(..., example="1.0.0")


class DetailedHealthModel(BaseModel):
    status: str = Field(..., example="healthy")
    timestamp: float = Field(..., example=1731465600.1234)
    service: str = Field(..., example="llm-classification")
    model: str = Field(..., example="claude-3-5-sonnet-20241022")
    aws_region: Optional[str] = Field(None, example="ap-southeast-1")


# ------------------------------------------------------------------------------
# App lifecycle
# ------------------------------------------------------------------------------
prediction_service: Optional[PredictionService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global prediction_service
    logger.info("Starting LLM Classification Service...")
    try:
        prediction_service = PredictionService()
        logger.info("Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service: {str(e)}")
        raise
    yield
    logger.info("Shutting down LLM Classification Service...")


# ------------------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------------------
app = FastAPI(
    title="LLM Document Classification Service",
    description="Claude Sonnet 4 powered document classification with hierarchical taxonomy",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.get(
    "/",
    response_model=RootHealthModel,
    response_model_exclude_none=True,
    summary="Root",
    description="Health check endpoint",
)
async def root():
    return {
        "service": "LLM Document Classification",
        "status": "healthy",
        "model": Config.CLAUDE_MODEL_ID,
        "version": "1.0.0",
    }


@app.get(
    "/health",
    response_model=DetailedHealthModel,
    response_model_exclude_none=True,
    summary="Health Check",
    description="Detailed health check",
)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "llm-classification",
        "model": Config.CLAUDE_MODEL_ID,
        "aws_region": Config.AWS_REGION,
    }


@app.post(
    "/predict",
    # IMPORTANT: don't use response_model here so docs don't derive schema from Dict/Any
    response_model=None,
    summary="Predict Document",
    description=(
        "Classify document using Claude Sonnet 4\n\n"
        "Args: request with text, predict levels, and optional context\n\n"
        "Returns: Classification results with timing and confidence scores"
    ),
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "elapsed_seconds": 1.23,
                        "predictions": {
                            "primary": [
                                {
                                    "pred": "Recommendations › Analyst Recommendation › Buy",
                                    "confidence": 0.92,
                                    "reasoning": "Explicit BUY statement with target price.",
                                    "key_evidence": {
                                        "supporting": [
                                            "We initiate coverage with a BUY rating.",
                                            "Target price implies 18% upside."
                                        ]
                                    },
                                }
                            ],
                            "secondary": [
                                {
                                    "pred": "News › Company › Earnings",
                                    "confidence": 0.78,
                                    "reasoning": "Mentions quarterly revenue and guidance.",
                                    "key_evidence": {
                                        "supporting": [
                                            "Q3 revenue of $4.2B.",
                                            "Guidance raised for FY25."
                                        ]
                                    },
                                }
                            ],
                            "tertiary": [],
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {"loc": ["body", "text"], "msg": "field required", "type": "value_error.missing"}
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal Error",
            "content": {"application/json": {"example": {"detail": "Classification failed: <reason>"}}},
        },
    },
)
async def predict_document(
    request: PredictionRequest = Body(
        ...,
        example={
            "text": "Acme Corp reported quarterly revenue of $4.2B and issued a BUY recommendation for XYZ.",
            "predict": ["primary", "secondary"],
            "context": {
                "company": "Acme Corp",
                "date": "2025-01-01",
                "analyst": "Jane Doe",
            },
        },
    )
):
    """
    Classify document using Claude Sonnet 4

    Returns the same structure as the 200 example above.
    """
    global prediction_service

    if prediction_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        logger.info(f"Received prediction request for levels: {request.predict}")
        logger.info(f"Context provided: {request.context}")
        logger.info(f"Text length (raw): {len(request.text)} characters")

        # Validate request
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        if not request.predict:
            raise HTTPException(status_code=400, detail="Must specify at least one prediction level")

        valid_levels = {"primary", "secondary", "tertiary"}
        for level in request.predict:
            if level not in valid_levels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid prediction level: {level}. Must be one of: {valid_levels}",
                )

        # Preprocess text
        preprocessed_text = clean_text(request.text, max_words=5000)
        logger.info(f"Text length (preprocessed): {len(preprocessed_text)} characters")

        # Make prediction (runtime behavior unchanged)
        result: dict = PredictionService().predict(
            text=preprocessed_text,
            predict_levels=request.predict,
            context=request.context,
        )

        logger.info(f"Prediction completed in {result['elapsed_seconds']:.2f}s")

        # Return raw dict so it matches the example (no response_model filtering)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


# ------------------------------------------------------------------------------
# Global exception handler
# ------------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5005, reload=True, log_level="info")
