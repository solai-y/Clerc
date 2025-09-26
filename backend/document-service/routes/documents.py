import logging
from flask import Blueprint, request
from models.document import DocumentModel
from models.response import APIResponse
from services.database import DatabaseService

documents_bp = Blueprint('documents', __name__)
logger = logging.getLogger(__name__)

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
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)
        search = request.args.get('search', type=str)
        status = request.args.get('status', type=str)
        company_id = request.args.get('company_id', type=int)
        
        if limit is not None and limit <= 0:
            return APIResponse.validation_error("Limit must be greater than 0")
        if offset is not None and offset < 0:
            return APIResponse.validation_error("Offset must be non-negative")
        
        total_count, count_error = db_service.get_total_documents_count(search, status, company_id)
        if count_error:
            logger.error(f"Database error getting count: {count_error}")
            return APIResponse.internal_error("Failed to retrieve documents count")
        
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
        
        current_limit = limit or 50
        current_offset = offset or 0
        current_page = (current_offset // current_limit) + 1
        total_pages = (total_count + current_limit - 1) // current_limit
        
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
        return APIResponse.success(document, "Document retrieved successfully")
    except Exception as e:
        logger.error(f"Unexpected error in get_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('', methods=['POST'])
def create_document():
    logger.info(f"POST /documents - Request from {request.remote_addr}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        try:
            data = request.get_json()
        except Exception as json_error:
            return APIResponse.validation_error(f"Invalid JSON format: {str(json_error)}")
        if not data:
            return APIResponse.validation_error("Request body cannot be empty")
        document_model = DocumentModel(data)
        is_valid, errors = document_model.validate()
        if not is_valid:
            return APIResponse.validation_error("; ".join(errors))
        created_document, error = db_service.create_document(document_model.to_dict())
        if error:
            logger.error(f"Database error: {error}")
            return APIResponse.internal_error("Failed to create document")
        return APIResponse.success(created_document, "Document created successfully", 201)
    except Exception as e:
        logger.error(f"Unexpected error in create_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    logger.info(f"PUT /documents/{document_id} - Request from {request.remote_addr}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        try:
            data = request.get_json()
        except Exception as json_error:
            return APIResponse.validation_error(f"Invalid JSON format: {str(json_error)}")
        if not data:
            return APIResponse.validation_error("Request body cannot be empty")
        data['document_id'] = document_id
        document_model = DocumentModel(data)
        is_valid, errors = document_model.validate()
        if not is_valid:
            return APIResponse.validation_error("; ".join(errors))
        updated_document, error = db_service.update_document(document_id, document_model.to_dict())
        if error:
            if "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            else:
                logger.error(f"Database error: {error}")
                return APIResponse.internal_error("Failed to update document")
        return APIResponse.success(updated_document, "Document updated successfully")
    except Exception as e:
        logger.error(f"Unexpected error in update_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
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
        return APIResponse.success(None, "Document deleted successfully")
    except Exception as e:
        logger.error(f"Unexpected error in delete_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>/status', methods=['PATCH'])
def update_document_status(document_id):
    logger.info(f"PATCH /documents/{document_id}/status - Request from {request.remote_addr}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        try:
            data = request.get_json()
        except Exception as json_error:
            return APIResponse.validation_error(f"Invalid JSON format: {str(json_error)}")
        if not data or 'status' not in data:
            return APIResponse.validation_error("Status field is required")
        status = data.get('status')
        if not isinstance(status, str):
            return APIResponse.validation_error("Status must be a string")
        success, error = db_service.update_document_status(document_id, status)
        if not success:
            if error and "not found" in error.lower():
                return APIResponse.not_found(f"Document with ID {document_id}")
            elif error and "Invalid status" in error:
                return APIResponse.validation_error(error)
            else:
                logger.error(f"Database error: {error}")
                return APIResponse.internal_error("Failed to update document status")
        return APIResponse.success(None, f"Document status updated to '{status}'")
    except Exception as e:
        logger.error(f"Unexpected error in update_document_status: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/processed', methods=['POST'])
def create_processed_document():
    logger.info(f"POST /documents/processed - Request from {request.remote_addr}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        try:
            data = request.get_json()
        except Exception as json_error:
            return APIResponse.validation_error(f"Invalid JSON format: {str(json_error)}")
        if not data:
            return APIResponse.validation_error("Request body cannot be empty")
        if 'document_id' not in data:
            return APIResponse.validation_error("document_id field is required")
        created_document, error = db_service.create_processed_document(data)
        if error:
            logger.error(f"Database error: {error}")
            return APIResponse.internal_error("Failed to create processed document")
        return APIResponse.success(created_document, "Processed document created successfully", 201)
    except Exception as e:
        logger.error(f"Unexpected error in create_processed_document: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>/tags', methods=['PATCH', 'OPTIONS'])
def update_document_tags(document_id):
    if request.method == 'OPTIONS':
        return '', 200
    logger.info(f"PATCH /documents/{document_id}/tags - Request from {request.remote_addr}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        if not request.is_json:
            return APIResponse.validation_error("Request must be JSON")
        try:
            data = request.get_json()
        except Exception as json_error:
            return APIResponse.validation_error(f"Invalid JSON format: {str(json_error)}")
        if not data:
            return APIResponse.validation_error("Request body cannot be empty")
        tag_fields = ['confirmed_tags', 'user_added_labels', 'user_removed_tags']
        if not any(f in data for f in tag_fields):
            return APIResponse.validation_error(f"At least one of the following fields is required: {', '.join(tag_fields)}")
        for f in tag_fields:
            if f in data and not isinstance(data[f], list):
                return APIResponse.validation_error(f"{f} must be an array")
        updated_document, error = db_service.update_document_tags(document_id, data)
        if error:
            if "not found" in error.lower() or "no processed document found" in error.lower():
                return APIResponse.not_found(f"Processed document for document_id {document_id}")
            else:
                logger.error(f"Database error: {error}")
                return APIResponse.internal_error("Failed to update document tags")
        return APIResponse.success(updated_document, "Document tags updated successfully")
    except Exception as e:
        logger.error(f"Unexpected error in update_document_tags: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/unprocessed', methods=['GET'])
def get_unprocessed_documents():
    logger.info(f"GET /documents/unprocessed - Request from {request.remote_addr}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        limit = request.args.get('limit', default=1, type=int)
        if limit <= 0:
            return APIResponse.validation_error("Limit must be greater than 0")
        unprocessed_docs, error = db_service.get_unprocessed_documents(limit)
        if error:
            logger.error(f"Database error: {error}")
            return APIResponse.internal_error("Failed to retrieve unprocessed documents")
        if not unprocessed_docs:
            return APIResponse.not_found("No unprocessed documents found")
        return APIResponse.success({
            "unprocessed_documents": unprocessed_docs,
            "count": len(unprocessed_docs)
        }, f"Retrieved {len(unprocessed_docs)} unprocessed document(s)")
    except Exception as e:
        logger.error(f"Unexpected error in get_unprocessed_documents: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/<int:document_id>/explanations', methods=['GET'])
def get_document_explanations(document_id):
    logger.info(f"GET /documents/{document_id}/explanations - Request from {request.remote_addr}")
    if not db_service:
        return APIResponse.internal_error("Database service not available")
    try:
        explanations, error = db_service.get_explanations_for_document(document_id)
        if error:
            logger.error(f"Database error: {error}")
            return APIResponse.internal_error("Failed to retrieve explanations")
        if not explanations:
            return APIResponse.success([], "No explanations found for this document")
        return APIResponse.success(explanations, f"Retrieved {len(explanations)} explanations")
    except Exception as e:
        logger.error(f"Unexpected error in get_document_explanations: {str(e)}")
        return APIResponse.internal_error()

@documents_bp.route('/test', methods=['GET'])
def test_route():
    return APIResponse.success({"test": "explanations route working"}, "Test successful")
