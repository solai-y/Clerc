"""
Configuration module for LLM Service
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") 
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # Model Configuration
    CLAUDE_MODEL_ID = os.getenv("CLAUDE_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
    
    # Service Configuration
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
    RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "10"))
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    
    # API Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

# Tag hierarchy structure
TAG_HIERARCHY: Dict[str, Any] = {
    "Disclosure": {
        "Annual_Reports": [],
        "Financial_Statements": [],
        "SEC_Filings": ["10-K", "10-Q", "S-1"],
        "Transcripts": ["AGM Transcripts", "Conference Transcripts", "Earnings Call Transcripts"],
        "Tearsheet": []
    },
    "News": {
        "Company": ["Management_Change", "Product_Launch"],
        "Industry": ["Energy", "Healthcare", "Information_Technology", "Real_Estate", "Regulation", "Supply_Chain"],
        "Macroeconomic": ["Employment", "Geopolitics", "Interest_Rates"]
    },
    "Recommendations": {
        "Analyst_Recommendations": ["Buy", "Hold", "Sell"],
        "Strategic_Recommendations": ["M&A Rationale", "Product Strategy"]
    }
}