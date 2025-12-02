# Text Extraction Service

FastAPI-based microservice for extracting text content from PDF documents with OCR fallback support.

## Overview

The Text Extraction Service extracts text from PDF documents using PyMuPDF (fitz) for direct text extraction and Tesseract OCR for scanned documents. It provides robust text extraction capabilities essential for the document classification pipeline.

## Key Features

- Direct text extraction from native PDFs (PyMuPDF)
- OCR fallback for scanned/image-based PDFs (Tesseract)
- Automatic text quality detection
- URL-based and file-based extraction
- Comprehensive error handling and logging

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `POST` | `/extract-text` | Extract text from PDF (URL or file) |

## Request Format

**POST /extract-text**

```json
{
  "pdf_url": "https://example.com/document.pdf"
}
```

or with direct file upload via multipart/form-data.

## Response Format

```json
{
  "text": "Extracted document text...",
  "method": "direct",  // or "ocr"
  "pages": 15,
  "char_count": 45000
}
```

## Environment Variables

```env
PORT=5008
```

Optional (for OCR functionality):
- Tesseract OCR must be installed on the system
- pdf2image and PIL dependencies

## Running Locally

**With Docker:**
```bash
cd backend
docker-compose up -d text-extraction-service
```

**Standalone:**
```bash
cd backend/text-extraction-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5008
```

## Service Configuration

- **Port:** 5008
- **Framework:** FastAPI
- **Dependencies:** PyMuPDF (fitz), pytesseract (optional), pdf2image (optional)

## OCR Support

OCR is automatically enabled if dependencies are available:
- `pytesseract`
- `pdf2image`
- `Pillow`

If OCR dependencies are missing, the service will still function with direct text extraction only.

## Extract Example

```bash
curl -X POST "http://localhost:5008/extract-text" \
  -H "Content-Type: application/json" \
  -d '{"pdf_url": "https://example.com/report.pdf"}'
```

## API Documentation

Once running, view interactive API docs at:
- Swagger UI: `http://localhost:5008/docs`
- ReDoc: `http://localhost:5008/redoc`

## Health Check

```bash
curl http://localhost:5008/health
```
