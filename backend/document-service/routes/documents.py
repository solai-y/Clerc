import logging
import os
import httpx
from fastapi import APIRouter, HTTPException, Request, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from models.document import DocumentModel
from models.response import APIResponse
from services.database import DatabaseService

# --------------------------------------------------------------------
# Pydantic models for request validation
# --------------------------------------------------------------------
class DocumentCreateRequest(BaseModel):
    document_name: str
    document_type: str
    link: str
    uploaded_by: Optional[int] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    upload_date: Optional[str] = None
    status: Optional[str] = 'uploaded'


class DocumentUpdateRequest(BaseModel):
    document_name: Optional[str] = None
    document_type: Optional[str] = None
    link: Optional[str] = None
    uploaded_by: Optional[int] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    upload_date: Optional[str] = None
    status: Optional[str] = None


class DocumentStatusRequest(BaseModel):
    status: str


class ProcessedDocumentRequest(BaseModel):
    document_id: int
    suggested_tags: Optional[list] = None
    threshold_pct: Optional[int] = None
    ocr_used: Optional[bool] = None
    processing_ms: Optional[int] = None
    explanations: Optional[list] = None
    prediction_response: Optional[dict] = None
    model_id: Optional[int] = None
    user_id: Optional[int] = None
    company: Optional[int] = None
    errors: Optional[list] = None
    request_id: Optional[str] = None
    status: Optional[str] = None


class DocumentTagsRequest(BaseModel):
    confirmed_tags: Optional[Any] = None
    user_added_labels: Optional[list] = None
    user_removed_tags: Optional[list] = None
    user_id: Optional[int] = None
    explanations: Optional[Any] = None


# ✅ New explicit model for PATCH /documents/{document_id}/timing
class TimingUpdateRequest(BaseModel):
    timingMs: int = Field(..., example=1530, description="Upload-to-confirmation time in milliseconds")


# --------------------------------------------------------------------
# Initialize router, logger, and database service
# --------------------------------------------------------------------
documents_router = APIRouter()
logger = logging.getLogger(__name__)

try:
    db_service = DatabaseService()
except Exception as e:
    logger.error(f"Failed to initialize database service: {str(e)}")
    db_service = None


# --------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------
@documents_router.get('')
async def get_documents(
    request: Request,
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
    sort_by: str = Query('date'),
    sort_order: str = Query('desc'),
    primary_tags: Optional[List[str]] = Query(None, alias="primary_tags[]"),
    secondary_tags: Optional[List[str]] = Query(None, alias="secondary_tags[]"),
    tertiary_tags: Optional[List[str]] = Query(None, alias="tertiary_tags[]")
):
    """List documents with search, filter, sort, and pagination."""
    logger.info(f"GET /documents - Request from {request.client.host}")

    if not db_service:
        return APIResponse.internal_error("Database service not available")

    try:
        primary_tags = primary_tags or []
        secondary_tags = secondary_tags or []
        tertiary_tags = tertiary_tags or []

        # Basic validations
        if limit is not None and limit <= 0:
            return APIResponse.validation_error("Limit must be greater than 0")
        if offset is not None and offset < 0:
            return APIResponse.validation_error("Offset must be non-negative")
        if sort_by not in (None, 'name', 'date', 'size'):
            return APIResponse.validation_error("sort_by must be one of: name, date, size")
        if sort_order not in (None, 'asc', 'desc'):
            return APIResponse.validation_error("sort_order must be 'asc' or 'desc'")

        total_count, count_error = db_service.get_total_documents_count(
            search=search, status=status, company_id=company_id,
            primary_tags=primary_tags, secondary_tags=secondary_tags, tertiary_tags=tertiary_tags
        )
        if count_error:
            return APIResponse.internal_error("Failed to retrieve documents count")

        documents, error = db_service.query_documents(
            search=search, status=status, company_id=company_id,
            sort_by=sort_by, sort_order=sort_order, limit=limit, offset=offset,
            primary_tags=primary_tags, secondary_tags=secondary_tags, tertiary_tags=tertiary_tags
        )
        if error:
            return APIResponse.internal_error("Failed to retrieve documents")

        current_limit = limit or 50
        current_offset = offset or 0
        current_page = (current_offset // current_limit) + 1
        total_pages = (total_count + current_limit - 1) // current_limit

        pagination_info = {
            "total": total_count, "page": current_page, "totalPages": total_pages,
            "limit": current_limit, "offset": current_offset
        }

        return APIResponse.success({"documents": documents, "pagination": pagination_info}, "Documents retrieved")

    except Exception as e:
        logger.error(f"Unexpected error in get_documents: {str(e)}")
        return APIResponse.internal_error()


@documents_router.get('/{document_id}')
async def get_document(document_id: int, request: Request):
    """Get a specific document by ID."""
    logger.info(f"GET /documents/{document_id}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        document, error = db_service.get_document_by_id(document_id)
        if error:
            if "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            return APIResponse.internal_error("Failed to retrieve document")
        return APIResponse.success(document, "Document retrieved successfully")
    except Exception as e:
        logger.error(f"Unexpected error in get_document: {str(e)}")
        return APIResponse.internal_error()


@documents_router.get('/{document_id}/complete')
async def get_complete_document(document_id: int, request: Request):
    """Get full document info (raw + processed)."""
    logger.info(f"GET /documents/{document_id}/complete")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        document, error = db_service.get_complete_document_by_id(document_id)
        if error:
            if "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            return APIResponse.internal_error("Failed to retrieve complete document")
        return APIResponse.success(document, "Complete document retrieved successfully")
    except Exception as e:
        logger.error(f"Unexpected error in get_complete_document: {str(e)}")
        return APIResponse.internal_error()


@documents_router.post('', status_code=201)
async def create_document(request: Request, body: DocumentCreateRequest):
    """Create a new document."""
    logger.info(f"POST /documents")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        data = body.dict()
        document_model = DocumentModel(data)
        is_valid, errors = document_model.validate()
        if not is_valid:
            return APIResponse.validation_error("; ".join(errors))
        created_document, error = db_service.create_document(document_model.to_dict())
        if error:
            return APIResponse.internal_error("Failed to create document")
        return APIResponse.success(created_document, "Document created successfully", 201)
    except Exception as e:
        logger.error(f"Unexpected error in create_document: {str(e)}")
        return APIResponse.internal_error()


@documents_router.put('/{document_id}')
async def update_document(document_id: int, request: Request, body: DocumentUpdateRequest):
    """Update an existing document."""
    logger.info(f"PUT /documents/{document_id}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        data = body.dict(exclude_unset=True)
        document_model = DocumentModel({**data, "document_id": document_id})
        is_valid, errors = document_model.validate()
        if not is_valid:
            return APIResponse.validation_error("; ".join(errors))
        updated_document, error = db_service.update_document(document_id, document_model.to_dict())
        if error:
            if "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            return APIResponse.internal_error("Failed to update document")
        return APIResponse.success(updated_document, "Document updated successfully")
    except Exception as e:
        logger.error(f"Unexpected error in update_document: {str(e)}")
        return APIResponse.internal_error()


@documents_router.delete('/{document_id}')
async def delete_document(document_id: int, request: Request):
    """Delete a document."""
    logger.info(f"DELETE /documents/{document_id}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        success, error = db_service.delete_document(document_id)
        if not success:
            if error and "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            return APIResponse.internal_error("Failed to delete document")
        return APIResponse.success(None, "Document deleted successfully")
    except Exception as e:
        logger.error(f"Unexpected error in delete_document: {str(e)}")
        return APIResponse.internal_error()


@documents_router.patch('/{document_id}/status')
async def update_document_status(document_id: int, request: Request, body: DocumentStatusRequest):
    """Update document status."""
    logger.info(f"PATCH /documents/{document_id}/status")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        success, error = db_service.update_document_status(document_id, body.status)
        if not success:
            if error and "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            elif error and "Invalid status" in error:
                return APIResponse.validation_error(error)
            return APIResponse.internal_error("Failed to update document status")
        return APIResponse.success(None, f"Document status updated to '{body.status}'")
    except Exception as e:
        logger.error(f"Unexpected error in update_document_status: {str(e)}")
        return APIResponse.internal_error()


@documents_router.post('/processed', status_code=201)
async def create_processed_document(request: Request, body: ProcessedDocumentRequest):
    """Create a processed document record."""
    logger.info("POST /documents/processed")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        created_document, error = db_service.create_processed_document(body.dict())
        if error:
            return APIResponse.internal_error("Failed to create processed document")
        return APIResponse.success(created_document, "Processed document created successfully", 201)
    except Exception as e:
        logger.error(f"Unexpected error in create_processed_document: {str(e)}")
        return APIResponse.internal_error()


# ✅ Fixed route: properly typed request model
@documents_router.patch("/{document_id}/timing")
async def update_document_timing(document_id: int, request: Request, body: TimingUpdateRequest):
    """Update the timing column for a document (upload → tag confirmation time in ms)."""
    logger.info(f"PATCH /documents/{document_id}/timing - Request from {request.client.host}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        timing_ms = body.timingMs
        updated_document, error = db_service.update_document_timing(document_id, timing_ms)
        if error:
            if "not found" in error.lower():
                return APIResponse.not_found(f"Document {document_id} not found")
            return APIResponse.internal_error("Failed to update document timing")
        return APIResponse.success(updated_document, "Document timing updated successfully")
    except Exception as e:
        logger.error(f"Unexpected error in update_document_timing: {str(e)}")
        return APIResponse.internal_error()


@documents_router.patch('/{document_id}/tags')
async def update_document_tags(document_id: int, request: Request, body: DocumentTagsRequest):
    """Update confirmed_tags, user_added_labels, and user_removed_tags for a document."""
    logger.info(f"PATCH /documents/{document_id}/tags - Request from {request.client.host}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        data = body.dict(exclude_unset=True)
        tag_fields = ['confirmed_tags', 'user_added_labels', 'user_removed_tags']
        has_tag_field = any(field in data for field in tag_fields)
        if not has_tag_field:
            return APIResponse.validation_error(f"At least one of {', '.join(tag_fields)} is required")

        for field in tag_fields:
            if field in data:
                if field == 'confirmed_tags':
                    if not isinstance(data[field], (list, dict)):
                        return APIResponse.validation_error(f"{field} must be an array or object")
                elif not isinstance(data[field], list):
                    return APIResponse.validation_error(f"{field} must be an array")

        updated_document, error = db_service.update_document_tags(document_id, data)
        if error:
            if "not found" in error.lower() or "no processed document found" in error.lower():
                return APIResponse.not_found(f"Processed document for document_id {document_id}")
            return APIResponse.internal_error("Failed to update document tags")

        # Async retraining call
        if 'confirmed_tags' in data:
            try:
                retraining_url = os.getenv('RETRAINING_SERVICE_URL', 'http://retraining-service:5009')
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        f"{retraining_url}/retraining/update-tags",
                        json={"document_id": document_id, "confirmed_tags": data['confirmed_tags']}
                    )
            except Exception as retraining_error:
                logger.warning(f"Retraining update error (non-critical): {str(retraining_error)}")

        return APIResponse.success(updated_document, "Document tags updated successfully")
    except Exception as e:
        logger.error(f"Unexpected error in update_document_tags: {str(e)}")
        return APIResponse.internal_error()


@documents_router.get('/unprocessed')
async def get_unprocessed_documents(request: Request, limit: int = Query(1)):
    """Get raw documents that haven't been processed."""
    logger.info(f"GET /documents/unprocessed")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        if limit <= 0:
            return APIResponse.validation_error("Limit must be greater than 0")
        unprocessed_docs, error = db_service.get_unprocessed_documents(limit)
        if error:
            return APIResponse.internal_error("Failed to retrieve unprocessed documents")
        if not unprocessed_docs:
            return APIResponse.not_found("No unprocessed documents found")
        return APIResponse.success(
            {"unprocessed_documents": unprocessed_docs, "count": len(unprocessed_docs)},
            f"Retrieved {len(unprocessed_docs)} unprocessed document(s)"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_unprocessed_documents: {str(e)}")
        return APIResponse.internal_error()


@documents_router.get('/{document_id}/explanations')
async def get_document_explanations(document_id: int, request: Request):
    """Get explanations for a specific document."""
    logger.info(f"GET /documents/{document_id}/explanations")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        explanations, error = db_service.get_explanations_for_document(document_id)
        if error:
            return APIResponse.internal_error("Failed to retrieve explanations")
        if not explanations:
            return APIResponse.success([], "No explanations found for this document")
        return APIResponse.success(explanations, f"Retrieved {len(explanations)} explanations")
    except Exception as e:
        logger.error(f"Unexpected error in get_document_explanations: {str(e)}")
        return APIResponse.internal_error()


@documents_router.get('/test')
async def test_route():
    """Simple test route."""
    return APIResponse.success({"test": "explanations route working"}, "Test successful")
