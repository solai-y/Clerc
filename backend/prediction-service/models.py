"""
Pydantic models for request/response validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ConfidenceThresholds(BaseModel):
    """Confidence threshold configuration"""
    primary: Optional[float] = Field(None, ge=0.0, le=1.0, description="Primary level confidence threshold")
    secondary: Optional[float] = Field(None, ge=0.0, le=1.0, description="Secondary level confidence threshold")
    tertiary: Optional[float] = Field(None, ge=0.0, le=1.0, description="Tertiary level confidence threshold")

class PredictionRequest(BaseModel):
    """Request model for prediction endpoint"""
    text: str = Field(..., description="Document content text to classify")
    predict_levels: List[str] = Field(..., description="List of levels to predict: primary, secondary, tertiary")
    confidence_thresholds: Optional[ConfidenceThresholds] = Field(None, description="Optional confidence threshold overrides")

class ServiceCallInfo(BaseModel):
    """Information about a service call"""
    called: bool = Field(..., description="Whether the service was called")
    duration: Optional[float] = Field(None, description="Duration of the call in seconds")
    success: bool = Field(..., description="Whether the call was successful")
    levels_requested: Optional[List[str]] = Field(None, description="Levels requested from this service")

class PredictionLevel(BaseModel):
    """Individual prediction level response"""
    pred: str = Field(..., description="Predicted tag/label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(None, description="Reasoning for the classification")
    source: str = Field(..., description="Source service: 'ai' or 'llm'")
    primary: Optional[str] = Field(None, description="Primary context for secondary/tertiary")
    secondary: Optional[str] = Field(None, description="Secondary context for tertiary")
    ai_prediction: Optional[Dict[str, Any]] = Field(None, description="Original AI prediction if available")
    llm_prediction: Optional[Dict[str, Any]] = Field(None, description="LLM prediction if available")

class PredictionResponse(BaseModel):
    """Complete prediction response"""
    primary: Optional[PredictionLevel] = None
    secondary: Optional[PredictionLevel] = None
    tertiary: Optional[PredictionLevel] = None

class ConfidenceAnalysis(BaseModel):
    """Analysis of confidence thresholds and triggering"""
    triggered_llm: bool = Field(..., description="Whether LLM was triggered")
    trigger_level: Optional[str] = Field(None, description="Which level triggered LLM call")
    levels_below_threshold: List[str] = Field(default_factory=list, description="Levels that were below threshold")

class ServiceCalls(BaseModel):
    """Information about all service calls made"""
    ai_service: ServiceCallInfo
    llm_service: ServiceCallInfo

class FullPredictionResponse(BaseModel):
    """Complete prediction service response"""
    prediction: PredictionResponse = Field(..., description="Prediction results")
    elapsed_seconds: float = Field(..., description="Total time taken for prediction")
    processed_text: str = Field(..., description="The input text that was processed")
    service_calls: ServiceCalls = Field(..., description="Information about service calls made")
    confidence_analysis: ConfidenceAnalysis = Field(..., description="Analysis of confidence evaluation")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: float = Field(..., description="Timestamp of health check")
    downstream_services: Dict[str, str] = Field(..., description="Status of downstream services")

class ConfigResponse(BaseModel):
    """Configuration response"""
    default_thresholds: Dict[str, float] = Field(..., description="Default confidence thresholds")
    service_urls: Dict[str, str] = Field(..., description="Downstream service URLs")
    timeouts: Dict[str, int] = Field(..., description="Service timeouts")

class UpdateThresholdsRequest(BaseModel):
    """Request model for updating confidence thresholds"""
    primary: Optional[float] = Field(None, ge=0.0, le=1.0, description="Primary level confidence threshold")
    secondary: Optional[float] = Field(None, ge=0.0, le=1.0, description="Secondary level confidence threshold")
    tertiary: Optional[float] = Field(None, ge=0.0, le=1.0, description="Tertiary level confidence threshold")
    updated_by: Optional[str] = Field("api", description="User or system making the update")

class ThresholdConfigResponse(BaseModel):
    """Response model for threshold configuration"""
    primary: float = Field(..., description="Primary level confidence threshold")
    secondary: float = Field(..., description="Secondary level confidence threshold")
    tertiary: float = Field(..., description="Tertiary level confidence threshold")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="User who made the last update")

class ThresholdHistoryItem(BaseModel):
    """Individual threshold history item"""
    primary_threshold: float
    secondary_threshold: float
    tertiary_threshold: float
    updated_at: str
    updated_by: str

class ThresholdHistoryResponse(BaseModel):
    """Response model for threshold history"""
    history: List[ThresholdHistoryItem] = Field(..., description="List of threshold changes")
    total_count: int = Field(..., description="Total number of history records")

# Text Extraction Models

class TextExtractionRequest(BaseModel):
    """Request model for PDF text extraction"""
    pdf_url: str = Field(..., description="URL to PDF file (e.g., S3 URL)")

class TextExtractionResponse(BaseModel):
    """Response model for text extraction"""
    text: str = Field(..., description="Extracted text content")
    page_count: int = Field(..., description="Number of pages processed")
    character_count: int = Field(..., description="Number of characters extracted")