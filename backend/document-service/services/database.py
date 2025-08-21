import os
import logging
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    """Database operations service with error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("Database connection initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database connection: {str(e)}")
            raise
    
    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test database connection"""
        try:
            # Simple query to test connection
            response = self.supabase.table('raw_documents').select("document_id").limit(1).execute()
            self.logger.info("Database connection test successful")
            return True, None
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Database connection test failed: {error_msg}")
            return False, error_msg
    
    def get_total_documents_count(self, search: Optional[str] = None, status: Optional[str] = None, company_id: Optional[int] = None) -> tuple[int, Optional[str]]:
        """Get total count of documents with optional filters"""
        try:
            query = self.supabase.table('raw_documents').select("document_id", count="exact")
            
            if search:
                query = query.ilike('document_name', f'%{search}%')
            if status:
                query = query.eq('status', status)
            if company_id:
                query = query.eq('company', company_id)
            
            response = query.execute()
            total_count = response.count if response.count is not None else 0
            self.logger.info(f"Total documents count: {total_count}")
            return total_count, None
        except Exception as e:
            error_msg = f"Failed to get documents count: {str(e)}"
            self.logger.error(error_msg)
            return 0, error_msg

    def get_all_documents(self, limit: Optional[int] = None, offset: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get all documents with optional pagination"""
        try:
            query = self.supabase.table('raw_documents').select("*")
            
            if offset is not None and limit is not None:
                # Use range for pagination: range(start, end) where end is inclusive
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)
            
            response = query.execute()
            self.logger.info(f"Retrieved {len(response.data)} documents")
            return response.data, None
        except Exception as e:
            error_msg = f"Failed to retrieve documents: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg
    
    def get_document_by_id(self, document_id: int) -> tuple[Optional[Dict], Optional[str]]:
        """Get document by ID"""
        try:
            response = self.supabase.table('raw_documents').select("*").eq('document_id', document_id).execute()
            
            if response.data:
                self.logger.info(f"Retrieved document with ID: {document_id}")
                return response.data[0], None
            else:
                self.logger.warning(f"Document with ID {document_id} not found")
                return None, f"Document with ID {document_id} not found"
        except Exception as e:
            error_msg = f"Failed to retrieve document {document_id}: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    def create_document(self, document_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Create a new document"""
        try:
            response = self.supabase.table('raw_documents').insert(document_data).execute()
            
            if response.data:
                created_doc = response.data[0]
                self.logger.info(f"Created document with ID: {created_doc.get('id')}")
                return created_doc, None
            else:
                error_msg = "Failed to create document - no data returned"
                self.logger.error(error_msg)
                return None, error_msg
        except Exception as e:
            error_msg = f"Failed to create document: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    def update_document(self, document_id: int, document_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Update an existing document"""
        try:
            # First check if document exists
            existing_doc, error = self.get_document_by_id(document_id)
            if error:
                return None, error
            
            if not existing_doc:
                return None, f"Document with ID {document_id} not found"
            
            # Update the document
            response = self.supabase.table('raw_documents').update(document_data).eq('document_id', document_id).execute()
            
            if response.data:
                updated_doc = response.data[0]
                self.logger.info(f"Updated document with ID: {document_id}")
                return updated_doc, None
            else:
                error_msg = f"Failed to update document {document_id} - no data returned"
                self.logger.error(error_msg)
                return None, error_msg
        except Exception as e:
            error_msg = f"Failed to update document {document_id}: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    def delete_document(self, document_id: int) -> tuple[bool, Optional[str]]:
        """Delete a document"""
        try:
            # First check if document exists
            existing_doc, error = self.get_document_by_id(document_id)
            if error:
                return False, error
            
            if not existing_doc:
                return False, f"Document with ID {document_id} not found"
            
            # Delete the document
            response = self.supabase.table('raw_documents').delete().eq('document_id', document_id).execute()
            
            self.logger.info(f"Deleted document with ID: {document_id}")
            return True, None
        except Exception as e:
            error_msg = f"Failed to delete document {document_id}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def search_documents(self, search_term: str, limit: Optional[int] = None, offset: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Search documents by name (basic text search)"""
        try:
            query = self.supabase.table('raw_documents').select("*").ilike('document_name', f'%{search_term}%')
            
            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)
            
            response = query.execute()
            self.logger.info(f"Search for '{search_term}' returned {len(response.data)} documents")
            return response.data, None
        except Exception as e:
            error_msg = f"Failed to search documents: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg
    
    def get_documents_by_status(self, status: str, limit: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get documents by status"""
        try:
            query = self.supabase.table('raw_documents').select("*").eq('status', status)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            self.logger.info(f"Retrieved {len(response.data)} documents with status '{status}'")
            return response.data, None
        except Exception as e:
            error_msg = f"Failed to get documents by status: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg
    
    def get_documents_by_company(self, company_id: int, limit: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get documents by company ID"""
        try:
            query = self.supabase.table('raw_documents').select("*").eq('company', company_id)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            self.logger.info(f"Retrieved {len(response.data)} documents for company {company_id}")
            return response.data, None
        except Exception as e:
            error_msg = f"Failed to get documents by company: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg
    
    def update_document_status(self, document_id: int, status: str) -> tuple[bool, Optional[str]]:
        """Update document status"""
        try:
            valid_statuses = ['uploaded', 'processing', 'processed', 'failed']
            if status not in valid_statuses:
                return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            
            response = self.supabase.table('raw_documents').update({'status': status}).eq('document_id', document_id).execute()
            
            if response.data:
                self.logger.info(f"Updated document {document_id} status to '{status}'")
                return True, None
            else:
                return False, f"Document with ID {document_id} not found"
        except Exception as e:
            error_msg = f"Failed to update document status: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg