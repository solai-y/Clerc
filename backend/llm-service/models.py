"""
Pydantic models for request/response validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    """Request model for prediction endpoint"""
    text: str = Field(..., description="Preprocessed document content text")
    predict: List[str] = Field(..., description="List of levels to predict: primary, secondary, tertiary")
    context: Dict[str, str] = Field(default_factory=dict, description="Context with already predicted levels")

class KeyEvidence(BaseModel):
    """Key evidence structure for predictions"""
    supporting: List[Dict[str, str]] = Field(..., description="Supporting evidence tokens with impact")

class PredictionLevel(BaseModel):
    """Individual prediction level response"""
    pred: str = Field(..., description="Predicted tag/label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reasoning: Optional[str] = Field(None, description="Claude's reasoning for the classification")
    key_evidence: Optional[KeyEvidence] = Field(None, description="Evidence supporting the prediction (legacy)")
    primary: Optional[str] = Field(None, description="Primary tag context (for secondary/tertiary)")
    secondary: Optional[str] = Field(None, description="Secondary tag context (for tertiary only)")

class PredictionResponse(BaseModel):
    """Complete prediction response"""
    primary: Optional[PredictionLevel] = None
    secondary: Optional[PredictionLevel] = None
    tertiary: Optional[PredictionLevel] = None

class FullResponse(BaseModel):
    """Full response matching AI service format"""
    elapsed_seconds: float = Field(..., description="Time taken for prediction")
    prediction: PredictionResponse = Field(..., description="Prediction results")
    processed_text: str = Field(..., description="The input text that was processed")