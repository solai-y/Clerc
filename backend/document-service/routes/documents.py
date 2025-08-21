import logging
from flask import Blueprint, request, jsonify
from models.document import DocumentModel
from models.response import APIResponse
from services.database import DatabaseService

# Initialize blueprint and logger
documents_bp = Blueprint('documents', __name__)
logger = logging.getLogger(__name__)

# Initialize database service
try:
    db_service = DatabaseService()
except Exception as e:
    logger.error(f"Failed to initialize database service: {str(e)}")
    db_service = None

@documents_bp.route('', methods=['GET'])
def get_documents():
    """Get all documents with optional pagination and search"""
    logger.info(f"GET /documents - Request from {request.remote_addr}")
    
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    
    try:
        # Get query parameters
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)
        search = request.args.get('search', type=str)
        status = request.args.get('status', type=str)
        company_id = request.args.get('company_id', type=int)
        
        # Validate parameters
        if limit is not None and limit <= 0:
            return APIResponse.validation_error("Limit must be greater than 0")
        
        if offset is not None and offset < 0:
            return APIResponse.validation_error("Offset must be non-negative")
        
        # Get total count for pagination
        total_count, count_error = db_service.get_total_documents_count(search, status, company_id)
        if count_error:
            logger.error(f"Database error getting count: {count_error}")
            return APIResponse.internal_error("Failed to retrieve documents count")
        
        # Search, filter, or get all documents
        if search:
            documents, error = db_service.search_documents(search, limit, offset)
        elif status:
            documents, error = db_service.get_documents_by_status(status, limit)
        elif company_id:
            documents, error = db_service.get_documents_by_company(company_id, limit)
        else:
            documents, error = db_service.get_all_documents(limit, offset)
        
        if error:
            logger.error(f"Database error: {error}")
            return APIResponse.internal_error("Failed to retrieve documents")
        
        # Calculate pagination metadata
        current_limit = limit or 50
        current_offset = offset or 0
        current_page = (current_offset // current_limit) + 1
        total_pages = (total_count + current_limit - 1) // current_limit  # Ceiling division
        
        pagination_info = {
            "total": total_count,
            "page": current_page,
            "totalPages": total_pages,
            "limit": current_limit,
            "offset": current_offset
        }
        
        response_data = {
            "documents": documents,
            "pagination": pagination_info
        }
        
        logger.info(f"Successfully retrieved {len(documents)} of {total_count} documents (page {current_page}/{total_pages})")
        return APIResponse.success(response_data, f"Retrieved {len(documents)} of {total_count} documents")
        
    except Exception as e:
        logger.error(f"Unexpected error in get_documents: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Get a specific document by ID"""
    logger.info(f"GET /documents/{document_id} - Request from {request.remote_addr}")
    
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    
    try:
        document, error = db_service.get_document_by_id(document_id)
        
        if error:
            if "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            else:
                logger.error(f"Database error: {error}")
                return APIResponse.internal_error("Failed to retrieve document")
        
        logger.info(f"Successfully retrieved document {document_id}")
        return APIResponse.success(document, "Document retrieved successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error in get_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('', methods=['POST'])
def create_document():
    """Create a new document"""
    logger.info(f"POST /documents - Request from {request.remote_addr}")
    
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    
    try:
        # Validate request data
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        
        data = request.get_json()
        if not data:
            return APIResponse.validation_error("Request body cannot be empty")
        
        # Create and validate document model
        document_model = DocumentModel(data)
        is_valid, errors = document_model.validate()
        
        if not is_valid:
            return APIResponse.validation_error("; ".join(errors))
        
        # Create document in database
        created_document, error = db_service.create_document(document_model.to_dict())
        
        if error:
            logger.error(f"Database error: {error}")
            return APIResponse.internal_error("Failed to create document")
        
        logger.info(f"Successfully created document with ID: {created_document.get('id')}")
        return APIResponse.success(created_document, "Document created successfully", 201)
        
    except Exception as e:
        logger.error(f"Unexpected error in create_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    """Update an existing document"""
    logger.info(f"PUT /documents/{document_id} - Request from {request.remote_addr}")
    
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    
    try:
        # Validate request data
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        
        data = request.get_json()
        if not data:
            return APIResponse.validation_error("Request body cannot be empty")
        
        # Add ID to data for validation
        data['document_id'] = document_id
        
        # Create and validate document model
        document_model = DocumentModel(data)
        is_valid, errors = document_model.validate()
        
        if not is_valid:
            return APIResponse.validation_error("; ".join(errors))
        
        # Update document in database
        updated_document, error = db_service.update_document(document_id, document_model.to_dict())
        
        if error:
            if "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            else:
                logger.error(f"Database error: {error}")
                return APIResponse.internal_error("Failed to update document")
        
        logger.info(f"Successfully updated document {document_id}")
        return APIResponse.success(updated_document, "Document updated successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error in update_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document"""
    logger.info(f"DELETE /documents/{document_id} - Request from {request.remote_addr}")
    
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    
    try:
        success, error = db_service.delete_document(document_id)
        
        if not success:
            if error and "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            else:
                logger.error(f"Database error: {error}")
                return APIResponse.internal_error("Failed to delete document")
        
        logger.info(f"Successfully deleted document {document_id}")
        return APIResponse.success(None, "Document deleted successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>/status', methods=['PATCH'])
def update_document_status(document_id):
    """Update document status"""
    logger.info(f"PATCH /documents/{document_id}/status - Request from {request.remote_addr}")
    
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    
    try:
        # Validate request data
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        
        data = request.get_json()
        if not data or 'status' not in data:
            return APIResponse.validation_error("Status field is required")
        
        status = data.get('status')
        if not isinstance(status, str):
            return APIResponse.validation_error("Status must be a string")
        
        # Update document status
        success, error = db_service.update_document_status(document_id, status)
        
        if not success:
            if error and "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            elif error and "Invalid status" in error:
                return APIResponse.validation_error(error)
            else:
                logger.error(f"Database error: {error}")
                return APIResponse.internal_error("Failed to update document status")
        
        logger.info(f"Successfully updated document {document_id} status to '{status}'")
        return APIResponse.success(None, f"Document status updated to '{status}'")
        
    except Exception as e:
        logger.error(f"Unexpected error in update_document_status: {str(e)}")
        return APIResponse.internal_error()