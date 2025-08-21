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
        """Get total count of processed documents with optional filters"""
        try:
            query = self.supabase.table('processed_documents').select("process_id", count="exact")
            
            # For search and company filters, we need to join with raw_documents
            if search or company_id:
                query = query.select("process_id, raw_documents!document_id(document_name, company)", count="exact")
                if search:
                    # This is more complex with joins, may need to adjust based on Supabase capabilities
                    pass  # Will implement search filtering in the main query
                if company_id:
                    # Will implement company filtering in the main query  
                    pass
            
            if status:
                query = query.eq('status', status)
            
            response = query.execute()
            total_count = response.count if response.count is not None else 0
            self.logger.info(f"Total processed documents count: {total_count}")
            return total_count, None
        except Exception as e:
            error_msg = f"Failed to get processed documents count: {str(e)}"
            self.logger.error(error_msg)
            return 0, error_msg

    def get_all_documents(self, limit: Optional[int] = None, offset: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get all processed documents with document info from raw_documents"""
        try:
            # Query processed_documents as primary table and join with raw_documents for document info
            query = self.supabase.table('processed_documents').select("""
                *,
                raw_documents!document_id(
                    document_name,
                    document_type,
                    link,
                    uploaded_by,
                    company,
                    upload_date,
                    file_size,
                    file_hash,
                    status
                )
            """)
            
            if offset is not None and limit is not None:
                # Use range for pagination: range(start, end) where end is inclusive
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            # Fetch company names for documents that have company IDs
            if response.data:
                # Get unique company IDs
                company_ids = set()
                for doc in response.data:
                    if doc.get('raw_documents', {}).get('company'):
                        company_ids.add(doc['raw_documents']['company'])
                
                # Fetch company information if we have company IDs
                company_names = {}
                if company_ids:
                    companies_response = self.supabase.table('companies').select('company_id, company_name').in_('company_id', list(company_ids)).execute()
                    for company in companies_response.data:
                        company_names[company['company_id']] = company['company_name']
                
                # Add company names to the documents
                for doc in response.data:
                    if doc.get('raw_documents', {}).get('company'):
                        company_id = doc['raw_documents']['company']
                        doc['raw_documents']['companies'] = {
                            'company_id': company_id,
                            'company_name': company_names.get(company_id, 'Unknown Company')
                        }
                    else:
                        doc['raw_documents']['companies'] = None
            
            self.logger.info(f"Retrieved {len(response.data)} processed documents")
            return response.data, None
        except Exception as e:
            error_msg = f"Failed to retrieve processed documents: {str(e)}"
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
        """Search processed documents by document name"""
        try:
            # Query processed_documents and join with raw_documents, then filter by document name
            query = self.supabase.table('processed_documents').select("""
                *,
                raw_documents!document_id(
                    document_name,
                    document_type,
                    link,
                    uploaded_by,
                    company,
                    upload_date,
                    file_size,
                    file_hash,
                    status
                )
            """)
            
            # Note: Filtering by joined table fields in Supabase can be tricky
            # We'll get all processed documents first, then filter in Python
            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit * 5)  # Get more records to account for filtering
            
            response = query.execute()
            
            # Filter by document name in Python
            filtered_documents = []
            for doc in response.data:
                if (doc.get('raw_documents') and 
                    isinstance(doc['raw_documents'], dict) and
                    search_term.lower() in doc['raw_documents'].get('document_name', '').lower()):
                    filtered_documents.append(doc)
            
            # Apply limit after filtering
            if limit:
                filtered_documents = filtered_documents[:limit]
            
            self.logger.info(f"Search for '{search_term}' returned {len(filtered_documents)} processed documents")
            return filtered_documents, None
            
        except Exception as e:
            error_msg = f"Failed to search processed documents: {str(e)}"
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