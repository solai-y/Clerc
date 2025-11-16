from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------
load_dotenv()
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# -------------------------------------------------------------------
# Initialize FastAPI app
# -------------------------------------------------------------------
app = FastAPI(
    title="company-service",
    description="Company data management service",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Pydantic models for clean OpenAPI
# -------------------------------------------------------------------
class HealthResponse(BaseModel):
    message: str = Field(..., example="Company service is reachable")

class Company(BaseModel):
    id: int = Field(..., example=1)
    company_name: str = Field(..., example="SAP SE")
    company_website: Optional[str] = Field(None, example="https://www.sap.com")
    industry: Optional[str] = Field(None, example="Software")
    headquarters_country: Optional[str] = Field(None, example="Germany")
    region: Optional[str] = Field(None, example="EMEA")
    city: Optional[str] = Field(None, example="Walldorf")
    company_size_employees: Optional[int] = Field(None, example=100000)
    annual_revenue_usd: Optional[float] = Field(None, example=35000000000.0)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.get(
    "/e2e",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "E2E health check successful",
            "content": {
                "application/json": {
                    "example": {"message": "Company service is reachable"}
                }
            },
        }
    },
)
def e2e_test():
    """Health check endpoint"""
    return {"message": "Company service is reachable"}


@app.get(
    "/companies",
    response_model=List[Company],
    responses={
        200: {
            "description": "List of companies fetched successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "company_name": "SAP SE",
                            "company_website": "https://www.sap.com",
                            "industry": "Software",
                            "headquarters_country": "Germany",
                            "region": "EMEA",
                            "city": "Walldorf",
                            "company_size_employees": 100000,
                            "annual_revenue_usd": 35000000000.0
                        },
                        {
                            "id": 2,
                            "company_name": "Accenture",
                            "company_website": "https://www.accenture.com",
                            "industry": "Consulting",
                            "headquarters_country": "Ireland",
                            "region": "Global",
                            "city": "Dublin",
                            "company_size_employees": 733000,
                            "annual_revenue_usd": 62000000000.0
                        }
                    ]
                }
            },
        }
    },
)
def get_companies():
    """Fetch all companies from Supabase"""
    response = supabase.table('companies').select("*").execute()
    return response.data

# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
