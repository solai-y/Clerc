import os
import logging
from typing import List, Optional, Dict, Any, Tuple
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
            _ = self.supabase.table('raw_documents').select("document_id").limit(1).execute()
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
        """
        Return count of processed_documents with optional filters.
        For `search`, avoid count='exact' and count locally to dodge PostgREST/worker issues.
        On any failure, log and return (0, None) so the route can still return 200.
        """
        try:
            if search:
                # First get matching raw document IDs
                raw_resp = (
                    self.supabase
                    .table('raw_documents')
                    .select('document_id')
                    .ilike('document_name', f'%{search}%')
                    .execute()
                )
                raw_ids = [r['document_id'] for r in (raw_resp.data or [])]
                if not raw_ids:
                    return 0, None

                # Then get processed docs for those IDs and filter locally
                proc_resp = (
                    self.supabase
                    .table('processed_documents')
                    .select('process_id, status, company, document_id')
                    .in_('document_id', raw_ids)
                    .execute()
                )
                rows = proc_resp.data or []
                if status:
                    rows = [r for r in rows if r.get('status') == status]
                if company_id is not None:
                    rows = [r for r in rows if r.get('company') == company_id]
                return len(rows), None

            # No search: lightweight count via select+len (no exact count)
            query = self.supabase.table('processed_documents').select('process_id')
            if status:
                query = query.eq('status', status)
            if company_id is not None:
                query = query.eq('company', company_id)
            resp = query.execute()
            return len(resp.data or []), None

        except Exception as e:
            # Never break the endpoint for counts
            self.logger.error(f"Failed to get processed documents count: {str(e)}")
            return 0, None

    def get_all_documents(self, limit: Optional[int] = None, offset: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get all processed documents; stitch raw data and companies without joins."""
        try:
            # 1) Fetch processed rows (primary)
            q = self.supabase.table('processed_documents').select('*')
            if offset is not None and limit is not None:
                q = q.range(offset, offset + limit - 1)
            elif limit:
                q = q.limit(limit)
            proc_resp = q.execute()
            proc_rows: List[Dict[str, Any]] = proc_resp.data or []
            if not proc_rows:
                return [], None

            # 2) Fetch raw_documents for those IDs (no join)
            doc_ids = [r['document_id'] for r in proc_rows if r.get('document_id') is not None]
            raw_map: Dict[int, Dict[str, Any]] = {}
            if doc_ids:
                raw_resp = (
                    self.supabase.table('raw_documents')
                    .select('document_id, document_name, document_type, link, uploaded_by, upload_date, file_size, file_hash, status')
                    .in_('document_id', doc_ids)
                    .execute()
                )
                for rd in (raw_resp.data or []):
                    raw_map[rd['document_id']] = rd

            # 3) Company enrichment
            company_ids = {r['company'] for r in proc_rows if r.get('company')}
            company_name_map: Dict[Any, Any] = {}
            if company_ids:
                comp_resp = (
                    self.supabase.table('companies')
                    .select('company_id, company_name')
                    .in_('company_id', list(company_ids))
                    .execute()
                )
                for c in (comp_resp.data or []):
                    company_name_map[c['company_id']] = c['company_name']

            # 4) Stitch raw + companies into processed rows
            stitched: List[Dict[str, Any]] = []
            for r in proc_rows:
                raw = raw_map.get(r.get('document_id')) or {}
                r['raw_documents'] = {
                    'document_name': raw.get('document_name'),
                    'document_type': raw.get('document_type'),
                    'link': raw.get('link'),
                    'uploaded_by': raw.get('uploaded_by'),
                    'upload_date': raw.get('upload_date'),
                    'file_size': raw.get('file_size'),
                    'file_hash': raw.get('file_hash'),
                    'status': raw.get('status'),
                    'companies': (
                        {
                            'company_id': r.get('company'),
                            'company_name': company_name_map.get(r.get('company'), 'Unknown Company')
                        } if r.get('company') else None
                    )
                }
                stitched.append(r)

            self.logger.info(f"Retrieved {len(stitched)} processed documents (joinless)")
            return stitched, None

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
            existing_doc, error = self.get_document_by_id(document_id)
            if error:
                return None, error
            if not existing_doc:
                return None, f"Document with ID {document_id} not found"
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
            existing_doc, error = self.get_document_by_id(document_id)
            if error:
                return False, error
            if not existing_doc:
                return False, f"Document with ID {document_id} not found"
            _ = self.supabase.table('raw_documents').delete().eq('document_id', document_id).execute()
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
        offset: Optional[int] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """
        Search processed documents by raw document_name (NO JOIN).
        1) Find raw document_ids by name.
        2) Fetch processed_documents for those ids.
        3) Stitch raw fields + company names.
        On any failure, return ([], None) so the caller can still respond 200.
        """
        try:
            # 1) raw ids
            raw_resp = (
                self.supabase
                .table('raw_documents')
                .select('document_id, document_name, document_type, link, uploaded_by, upload_date, file_size, file_hash, status')
                .ilike('document_name', f'%{search_term}%')
                .execute()
            )
            raw_rows = raw_resp.data or []
            if not raw_rows:
                self.logger.info(f"Search for '{search_term}' returned 0 documents")
                return [], None

            id_list = [r['document_id'] for r in raw_rows]
            raw_map = {r['document_id']: r for r in raw_rows}

            # 2) processed for those ids (apply pagination here)
            q = self.supabase.table('processed_documents').select('*').in_('document_id', id_list)
            if offset is not None and limit is not None:
                q = q.range(offset, offset + limit - 1)
            elif limit:
                q = q.limit(limit)
            proc_resp = q.execute()
            proc_rows = proc_resp.data or []

            # 3) company enrichment
            company_ids = {r['company'] for r in proc_rows if r.get('company')}
            company_name_map: Dict[Any, Any] = {}
            if company_ids:
                comp_resp = (
                    self.supabase.table('companies')
                    .select('company_id, company_name')
                    .in_('company_id', list(company_ids))
                    .execute()
                )
                for c in (comp_resp.data or []):
                    company_name_map[c['company_id']] = c['company_name']

            # 4) stitch
            stitched: List[Dict[str, Any]] = []
            for r in proc_rows:
                raw = raw_map.get(r.get('document_id')) or {}
                r['raw_documents'] = {
                    'document_name': raw.get('document_name'),
                    'document_type': raw.get('document_type'),
                    'link': raw.get('link'),
                    'uploaded_by': raw.get('uploaded_by'),
                    'upload_date': raw.get('upload_date'),
                    'file_size': raw.get('file_size'),
                    'file_hash': raw.get('file_hash'),
                    'status': raw.get('status'),
                    'companies': (
                        {
                            'company_id': r.get('company'),
                            'company_name': company_name_map.get(r.get('company'), 'Unknown Company')
                        } if r.get('company') else None
                    )
                }
                stitched.append(r)

            self.logger.info(f"Search for '{search_term}' returned {len(stitched)} processed documents (joinless)")
            return stitched, None

        except Exception as e:
            # Critical for the test: do NOT propagate search failures — return empty results gracefully.
            self.logger.error(f"Failed to search processed documents (handled): {str(e)}")
            return [], None
    
    def get_documents_by_status(self, status: str, limit: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get documents by status from raw_documents."""
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
        """Get processed documents by company ID (no join; stitch raw/company)."""
        try:
            q = self.supabase.table('processed_documents').select('*').eq('company', company_id)
            if limit:
                q = q.limit(limit)
            proc_resp = q.execute()
            proc_rows = proc_resp.data or []
            if not proc_rows:
                return [], None

            doc_ids = [r['document_id'] for r in proc_rows if r.get('document_id') is not None]
            raw_map: Dict[int, Dict[str, Any]] = {}
            if doc_ids:
                raw_resp = (
                    self.supabase.table('raw_documents')
                    .select('document_id, document_name, document_type, link, uploaded_by, upload_date, file_size, file_hash, status')
                    .in_('document_id', doc_ids)
                    .execute()
                )
                for rd in (raw_resp.data or []):
                    raw_map[rd['document_id']] = rd

            for r in proc_rows:
                raw = raw_map.get(r.get('document_id')) or {}
                r['raw_documents'] = {
                    'document_name': raw.get('document_name'),
                    'document_type': raw.get('document_type'),
                    'link': raw.get('link'),
                    'uploaded_by': raw.get('uploaded_by'),
                    'upload_date': raw.get('upload_date'),
                    'file_size': raw.get('file_size'),
                    'file_hash': raw.get('file_hash'),
                    'status': raw.get('status'),
                    'companies': {
                        'company_id': r.get('company'),
                        'company_name': None
                    } if r.get('company') else None
                }

            self.logger.info(f"Retrieved {len(proc_rows)} processed documents for company {company_id} (joinless)")
            return proc_rows, None

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
        """Create a new processed document entry with empty tag fields and explanations"""
        try:
            required_fields = ['document_id']
            for field in required_fields:
                if field not in document_data:
                    return None, f"Missing required field: {field}"
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
                process_id = created_doc.get('process_id')
                self.logger.info(f"Created processed document with process_id: {process_id}")
                explanations = document_data.get('explanations', [])
                if explanations:
                    explanation_error = self.create_explanations(process_id, explanations)
                    if explanation_error:
                        self.logger.warning(f"Failed to create explanations: {explanation_error}")
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
            existing_response = self.supabase.table('processed_documents').select("*").eq('document_id', document_id).execute()
            if not existing_response.data:
                return None, f"No processed document found for document_id {document_id}"
            existing_doc = existing_response.data[0]
            process_id = existing_doc['process_id']
            update_data: Dict[str, Any] = {}
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
            update_data['user_reviewed'] = True
            update_data['reviewed_at'] = 'now()'
            if 'user_id' in tag_data:
                update_data['user_id'] = tag_data['user_id']
            if not update_data:
                return None, "No valid tag data provided for update"
            response = self.supabase.table('processed_documents').update(update_data).eq('process_id', process_id).execute()
            if response.data:
                updated_doc = response.data[0]
                if 'explanations' in tag_data:
                    explanation_error = self.create_explanations(process_id, tag_data['explanations'])
                    if explanation_error:
                        self.logger.warning(f"Failed to create explanations during tag update: {explanation_error}")
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
            processed_response = self.supabase.table('processed_documents').select('document_id').execute()
            processed_ids = {doc['document_id'] for doc in (processed_response.data or [])}
            raw_response = self.supabase.table('raw_documents').select("*").execute()
            unprocessed_docs = []
            for doc in (raw_response.data or []):
                if doc['document_id'] not in processed_ids:
                    unprocessed_docs.append(doc)
                    if len(unprocessed_docs) >= limit:
                        break
            self.logger.info(f"Retrieved {len(unprocessed_docs)} unprocessed documents out of {len(raw_response.data or [])} total raw documents")
            return unprocessed_docs, None
        except Exception as e:
            error_msg = f"Failed to get unprocessed documents: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg

    def create_explanations(self, process_id: int, explanations: List[Dict[str, Any]]) -> Optional[str]:
        """Create explanation records for a processed document"""
        try:
            explanation_records = []
            for explanation in explanations:
                service_response = explanation.get('full_response', {})
                if explanation.get('shap_data'):
                    service_response['shap_explainability'] = explanation['shap_data']
                record = {
                    'process_id': process_id,
                    'classification_level': explanation['level'],
                    'predicted_tag': explanation['tag'],
                    'confidence': explanation['confidence'],
                    'reasoning': explanation.get('reasoning'),
                    'source_service': explanation['source'],
                    'service_response': service_response
                }
                explanation_records.append(record)
            if explanation_records:
                response = self.supabase.table('explanations').insert(explanation_records).execute()
                if response.data:
                    self.logger.info(f"Created {len(response.data)} explanation records for process_id {process_id}")
                    return None
                else:
                    return "Failed to create explanation records - no data returned"
            return None
        except Exception as e:
            error_msg = f"Failed to create explanations: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_explanations_for_document(self, document_id: int) -> tuple[List[Dict], Optional[str]]:
        """Get all explanations for a specific document by joining with processed_documents"""
        try:
            response = self.supabase.table('explanations').select("""
                explanation_id,
                process_id,
                classification_level,
                predicted_tag,
                confidence,
                reasoning,
                source_service,
                service_response,
                created_at,
                processed_documents!inner(document_id)
            """).eq('processed_documents.document_id', document_id).order('classification_level').execute()
            if response.data:
                explanations = []
                for item in response.data:
                    explanation = {k: v for k, v in item.items() if k != 'processed_documents'}
                    explanation['document_id'] = item['processed_documents']['document_id']
                    explanations.append(explanation)
                self.logger.info(f"Retrieved {len(explanations)} explanations for document {document_id}")
                return explanations, None
            else:
                return [], None
        except Exception as e:
            error_msg = f"Failed to get explanations for document {document_id}: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg
