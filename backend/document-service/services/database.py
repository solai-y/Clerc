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
    
    def get_total_documents_count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        company_id: Optional[int] = None
    ) -> tuple[int, Optional[str]]:
        try:
            # If searching by name, first find matching raw doc IDs
            if search:
                raw_resp = (
                    self.supabase
                    .table('raw_documents')
                    .select('document_id', count='exact')
                    .ilike('document_name', f'%{search}%')
                    .execute()
                )
                raw_ids = [r['document_id'] for r in raw_resp.data]
                if not raw_ids:
                    return 0, None  # no matches at all

                # Count processed docs that match those raw IDs (and other filters)
                query = (
                    self.supabase
                    .table('processed_documents')
                    .select('process_id', count='exact')
                    .in_('document_id', raw_ids)
                )
                if status:
                    query = query.eq('status', status)
                if company_id:
                    query = query.eq('company', company_id)

                resp = query.execute()
                total_count = resp.count or 0
                self.logger.info(f"Filtered processed documents count (search): {total_count}")
                return total_count, None

            # No search: baseline count with optional filters
            query = self.supabase.table('processed_documents').select('process_id', count='exact')
            if status:
                query = query.eq('status', status)
            if company_id:
                query = query.eq('company', company_id)

            response = query.execute()
            total_count = response.count or 0
            self.logger.info(f"Total processed documents count: {total_count}")
            return total_count, None

        except Exception as e:
            error_msg = f"Failed to get processed documents count: {str(e)}"
            self.logger.error(error_msg)
            return 0, error_msg

    def get_all_documents(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """Get all processed documents with document info from raw_documents"""
        try:
            query = self.supabase.table('processed_documents').select("""
                *,
                raw_documents!document_id(
                    document_name,
                    document_type,
                    link,
                    uploaded_by,
                    upload_date,
                    file_size,
                    file_hash,
                    status
                )
            """)

            # Apply order before pagination
            query = self._apply_sort(query, sort_by, sort_order)

            # Pagination after ordering
            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()

            # Debug sample of returned order
            try:
                sample = response.data[:5] if response and response.data else []
                self.logger.info(
                    "Sort debug | sort_by=%s sort_order=%s | first=%s",
                    sort_by, sort_order,
                    [
                        {
                            "process_id": d.get("process_id"),
                            "name": (d.get("raw_documents") or {}).get("document_name"),
                            "date": (d.get("raw_documents") or {}).get("upload_date"),
                            "size": (d.get("raw_documents") or {}).get("file_size"),
                        }
                        for d in sample
                    ]
                )
            except Exception:
                pass

            # Company enrichment
            if response.data:
                company_ids = set()
                for doc in response.data:
                    if doc.get('company'):
                        company_ids.add(doc['company'])

                company_names = {}
                if company_ids:
                    companies_response = self.supabase.table('companies') \
                        .select('company_id, company_name') \
                        .in_('company_id', list(company_ids)).execute()
                    for company in companies_response.data:
                        company_names[company['company_id']] = company['company_name']

                for doc in response.data:
                    if doc.get('company'):
                        company_id = doc['company']
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
    
    def search_documents(
        self,
        search_term: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None 
    ) -> tuple[List[Dict], Optional[str]]:
        """Search processed documents by raw document_name, with correct pagination order."""
        try:
            # 1) Find matching raw document IDs
            raw_resp = (
                self.supabase
                .table('raw_documents')
                .select('document_id')
                .ilike('document_name', f'%{search_term}%')
                .execute()
            )
            raw_ids = [r['document_id'] for r in raw_resp.data]
            if not raw_ids:
                self.logger.info(f"Search for '{search_term}' returned 0 documents")
                return [], None

            # 2) Pull processed_documents for those IDs and join raw_documents
            query = (
                self.supabase
                .table('processed_documents')
                .select("""
                    *,
                    raw_documents!document_id(
                        document_name,
                        document_type,
                        link,
                        uploaded_by,
                        upload_date,
                        file_size,
                        file_hash,
                        status
                    )
                """)
                .in_('document_id', raw_ids)
            )

            # Order before paginate
            query = self._apply_sort(query, sort_by, sort_order)

            # Pagination
            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit is not None:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment
            if data:
                company_ids = {doc['company'] for doc in data if doc.get('company')}
                company_names = {}
                if company_ids:
                    companies_response = (
                        self.supabase
                        .table('companies')
                        .select('company_id, company_name')
                        .in_('company_id', list(company_ids))
                        .execute()
                    )
                    for c in companies_response.data:
                        company_names[c['company_id']] = c['company_name']

                for doc in data:
                    if doc.get('company'):
                        cid = doc['company']
                        doc.setdefault('raw_documents', {})
                        doc['raw_documents']['companies'] = {
                            'company_id': cid,
                            'company_name': company_names.get(cid, 'Unknown Company')
                        }
                    else:
                        doc.setdefault('raw_documents', {})
                        doc['raw_documents']['companies'] = None

            self.logger.info(f"Search for '{search_term}' returned {len(data)} processed documents")
            return data, None

        except Exception as e:
            error_msg = f"Failed to search processed documents: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg

    def get_documents_by_status(
        self,
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """Get processed documents by status with proper sorting/pagination."""
        try:
            query = self.supabase.table('processed_documents').select("""
                *,
                raw_documents!document_id(
                    document_name,
                    document_type,
                    link,
                    uploaded_by,
                    upload_date,
                    file_size,
                    file_hash,
                    status
                )
            """).eq('status', status)

            # Order before paginate
            query = self._apply_sort(query, sort_by, sort_order)

            # Pagination
            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment
            if data:
                company_ids = {doc['company'] for doc in data if doc.get('company')}
                company_names = {}
                if company_ids:
                    companies_response = (
                        self.supabase
                        .table('companies')
                        .select('company_id, company_name')
                        .in_('company_id', list(company_ids))
                        .execute()
                    )
                    for c in companies_response.data:
                        company_names[c['company_id']] = c['company_name']

                for doc in data:
                    if doc.get('company'):
                        cid = doc['company']
                        doc.setdefault('raw_documents', {})
                        doc['raw_documents']['companies'] = {
                            'company_id': cid,
                            'company_name': company_names.get(cid, 'Unknown Company')
                        }
                    else:
                        doc.setdefault('raw_documents', {})
                        doc['raw_documents']['companies'] = None

            self.logger.info(f"Retrieved {len(data)} processed documents with status '{status}'")
            return data, None

        except Exception as e:
            error_msg = f"Failed to get documents by status: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg

    def get_documents_by_company(
        self,
        company_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """Get processed documents by company ID with proper sorting/pagination."""
        try:
            query = self.supabase.table('processed_documents').select("""
                *,
                raw_documents!document_id(
                    document_name,
                    document_type,
                    link,
                    uploaded_by,
                    upload_date,
                    file_size,
                    file_hash,
                    status
                )
            """).eq('company', company_id)

            # Order before paginate
            query = self._apply_sort(query, sort_by, sort_order)

            # Pagination
            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment
            if data:
                for doc in data:
                    doc.setdefault('raw_documents', {})
                    doc['raw_documents']['companies'] = {
                        'company_id': company_id,
                        'company_name': None
                    }

            self.logger.info(f"Retrieved {len(data)} processed documents for company {company_id}")
            return data, None

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
    
    def create_processed_document(self, document_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Create a new processed document entry with empty tag fields"""
        try:
            # Validate required fields
            required_fields = ['document_id']
            for field in required_fields:
                if field not in document_data:
                    return None, f"Missing required field: {field}"
            
            # Prepare data with empty tag fields
            processed_data = {
                'document_id': document_data['document_id'],
                'model_id': document_data.get('model_id'),
                'threshold_pct': document_data.get('threshold_pct', 60),
                'suggested_tags': document_data.get('suggested_tags'),
                'confirmed_tags': [],
                'user_added_labels': [],
                'user_removed_tags': [],
                'user_reviewed': False,
                'user_id': document_data.get('user_id'),
                'company': document_data.get('company'),
                'ocr_used': document_data.get('ocr_used', False),
                'processing_ms': document_data.get('processing_ms'),
                'errors': document_data.get('errors'),
                'saved_training': document_data.get('saved_training', False),
                'saved_count': document_data.get('saved_count', 0),
                'request_id': document_data.get('request_id'),
                'status': document_data.get('status', 'api_processed')
            }
            
            response = self.supabase.table('processed_documents').insert(processed_data).execute()
            
            if response.data:
                created_doc = response.data[0]
                self.logger.info(f"Created processed document with process_id: {created_doc.get('process_id')}")
                return created_doc, None
            else:
                error_msg = "Failed to create processed document - no data returned"
                self.logger.error(error_msg)
                return None, error_msg
        except Exception as e:
            error_msg = f"Failed to create processed document: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    def update_document_tags(self, document_id: int, tag_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Update confirmed_tags, user_added_labels, and user_removed_tags for a processed document"""
        try:
            # First check if processed document exists for this document_id
            existing_response = self.supabase.table('processed_documents').select("*").eq('document_id', document_id).execute()
            
            if not existing_response.data:
                return None, f"No processed document found for document_id {document_id}"
            
            existing_doc = existing_response.data[0]
            process_id = existing_doc['process_id']
            
            # Prepare update data
            update_data = {}
            
            if 'confirmed_tags' in tag_data:
                if not isinstance(tag_data['confirmed_tags'], list):
                    return None, "confirmed_tags must be an array"
                update_data['confirmed_tags'] = tag_data['confirmed_tags']
            
            if 'user_added_labels' in tag_data:
                if not isinstance(tag_data['user_added_labels'], list):
                    return None, "user_added_labels must be an array"
                update_data['user_added_labels'] = tag_data['user_added_labels']
            
            if 'user_removed_tags' in tag_data:
                if not isinstance(tag_data['user_removed_tags'], list):
                    return None, "user_removed_tags must be an array"
                update_data['user_removed_tags'] = tag_data['user_removed_tags']
            
            # Mark as user reviewed and add review timestamp
            update_data['user_reviewed'] = True
            update_data['reviewed_at'] = 'now()'
            
            if 'user_id' in tag_data:
                update_data['user_id'] = tag_data['user_id']
            
            if not update_data:
                return None, "No valid tag data provided for update"
            
            # Update the processed document
            response = self.supabase.table('processed_documents').update(update_data).eq('process_id', process_id).execute()
            
            if response.data:
                updated_doc = response.data[0]
                self.logger.info(f"Updated tags for processed document {process_id} (document_id: {document_id})")
                return updated_doc, None
            else:
                error_msg = f"Failed to update processed document tags - no data returned"
                self.logger.error(error_msg)
                return None, error_msg
        except Exception as e:
            error_msg = f"Failed to update document tags: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    def get_unprocessed_documents(self, limit: int = 1) -> tuple[List[Dict], Optional[str]]:
        """Get raw documents that haven't been processed yet"""
        try:
            # Get all processed document IDs
            processed_response = self.supabase.table('processed_documents').select('document_id').execute()
            processed_ids = {doc['document_id'] for doc in processed_response.data}
            
            # Get all raw documents
            raw_response = self.supabase.table('raw_documents').select("*").execute()
            
            # Filter out already processed documents
            unprocessed_docs = []
            for doc in raw_response.data:
                if doc['document_id'] not in processed_ids:
                    unprocessed_docs.append(doc)
                    if len(unprocessed_docs) >= limit:
                        break
            
            self.logger.info(f"Retrieved {len(unprocessed_docs)} unprocessed documents out of {len(raw_response.data)} total raw documents")
            return unprocessed_docs, None
            
        except Exception as e:
            error_msg = f"Failed to get unprocessed documents: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg
        
    def _apply_sort(self, query, sort_by: str | None, sort_order: str | None):
        """
        Apply parent-level ordering by related raw_documents fields using table(column) syntax.
        This sorts the parent processed_documents rows by the child column, not just the embedded array.
        """
        # Defaults: name asc if unspecified by the caller
        by = (sort_by or 'name').lower()
        desc = (str(sort_order).lower() == 'desc') if sort_order else False

        # Map UI keys to child columns
        if by == 'name':
            primary = "raw_documents(document_name)"
        elif by == 'size':
            primary = "raw_documents(file_size)"
        elif by == 'date':
            primary = "raw_documents(upload_date)"
        else:
            # Fallback to parent
            primary = "process_id"

        # First order: parent by child column (or process_id)
        q = query.order(primary, desc=desc)

        # Stable secondary key on parent id (ascending for stability regardless of primary dir)
        q = q.order('process_id', desc=False)

        # Log how we applied sort for troubleshooting
        try:
            self.logger.info("Applied sort | primary=%s desc=%s | secondary=process_id.asc", primary, desc)
        except Exception:
            pass

        return q
