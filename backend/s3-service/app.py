from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime
import re

# ------------------------------------------------------------
# Load .env variables
# ------------------------------------------------------------
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# ------------------------------------------------------------
# FastAPI app with nicer OpenAPI metadata
# ------------------------------------------------------------
app = FastAPI(
    title="s3-service",
    description="File upload and storage",
    version="1.0.0",
)

# ------------------------------------------------------------
# S3 client
# ------------------------------------------------------------
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def secure_filename(filename: str) -> str:
    """Secure a filename by removing dangerous characters"""
    # Remove path components
    filename = filename.split("/")[-1].split("\\")[-1]
    # Allow only alphanumeric, dots, hyphens, and underscores
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename

# ------------------------------------------------------------
# Response models (so Swagger stops showing "string")
# ------------------------------------------------------------
class E2EResponse(BaseModel):
    message: str = Field(..., example="S3 service is reachable")

class UploadSuccessResponse(BaseModel):
    message: str = Field(..., example="File uploaded successfully")
    file_key: str = Field(..., example="uploads/report.pdf-20250101120000")
    s3_url: str = Field(
        ...,
        example="https://my-bucket.s3.ap-southeast-1.amazonaws.com/uploads/report.pdf-20250101120000",
    )

class ErrorResponse(BaseModel):
    detail: str = Field(..., example="File is not a PDF")

# ------------------------------------------------------------
# Endpoints (functionality unchanged)
# ------------------------------------------------------------
@app.get(
    "/e2e",
    response_model=E2EResponse,
    summary="E2E Test",
    description="Simple reachability check for s3-service.",
)
def e2e_test():
    return {"message": "S3 service is reachable"}

@app.post(
    "/upload",
    response_model=UploadSuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Server Error"},
    },
    summary="Upload File (PDF only)",
    description="Uploads a PDF (multipart/form-data) to S3 and returns its S3 key and public URL.",
)
async def upload_file(file: UploadFile = File(...)):
    # Check if the file is empty
    if not file.filename or file.filename == "":
        raise HTTPException(status_code=400, detail="Empty filename")

    # Check if file is pdf
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File is not a PDF")

    try:
        filename = secure_filename(file.filename)
        key = f"uploads/{filename}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Read file content
        file_content = await file.read()

        # Check file size max 100MB
        if len(file_content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File is too large")

        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=file.content_type,
            ContentDisposition="inline",
        )

        return {
            "message": "File uploaded successfully",
            "file_key": key,
            "s3_url": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}",
        }

    except HTTPException:
        # Re-raise expected HTTP errors (keeps your current behavior)
        raise
    except Exception as e:
        # Preserve your 500 error behavior
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5003)
