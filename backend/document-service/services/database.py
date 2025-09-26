import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    """Database operations service with error handling + server-side sort/search"""

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

    # ---------- Count (non-fatal on error) ----------

    def get_total_documents_count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        company_id: Optional[int] = None
    ) -> tuple[int, Optional[str]]:
        """
        Return count of processed_documents with optional filters.
        Be defensive: if anything fails (e.g., Cloudflare 1101), return 0 and an error string.
        The route will treat the error as non-fatal and continue with total=0.
        """
        try:
            if search:
                # Get raw IDs that match name, then count processed rows for those IDs.
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

                # Count processed rows client-side to avoid worker count issues
                proc = (
                    self.supabase
                    .table('processed_documents')
                    .select('process_id, status, company, document_id')
                    .in_('document_id', raw_ids)
                    .execute()
                )
                rows = proc.data or []
                if status:
                    rows = [r for r in rows if r.get('status') == status]
                if company_id:
                    rows = [r for r in rows if r.get('company') == company_id]
                return len(rows), None

            # No search: simpler count via select length
            query = self.supabase.table('processed_documents').select('process_id')
            if status:
                query = query.eq('status', status)
            if company_id:
                query = query.eq('company', company_id)
            resp = query.execute()
            return len(resp.data or []), None

        except Exception as e:
            msg = f"Failed to get processed documents count: {str(e)}"
            self.logger.error(msg)
            return 0, msg

    # ---------- Core getters (server-side join + sort) ----------

    def get_all_documents(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """Get all processed documents with raw info; server-side stable ordering."""
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

            query = self._apply_sort(query, sort_by, sort_order)

            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment (company now lives on processed_documents)
            if data:
                company_ids = {d['company'] for d in data if d.get('company')}
                company_names: Dict[Any, Any] = {}
                if company_ids:
                    companies = (
                        self.supabase.table('companies')
                        .select('company_id, company_name')
                        .in_('company_id', list(company_ids))
                        .execute()
                    )
                    for c in (companies.data or []):
                        company_names[c['company_id']] = c['company_name']

                for d in data:
                    rd = d.setdefault('raw_documents', {})
                    if d.get('company'):
                        cid = d['company']
                        rd['companies'] = {
                            'company_id': cid,
                            'company_name': company_names.get(cid, 'Unknown Company')
                        }
                    else:
                        rd['companies'] = None

            self.logger.info(f"Retrieved {len(data)} processed documents")
            return data, None

        except Exception as e:
            error_msg = f"Failed to retrieve processed documents: {str(e)}"
            self.logger.error(error_msg)
            return [], error_msg

    def get_document_by_id(self, document_id: int) -> tuple[Optional[Dict], Optional[str]]:
        """Get document by ID (raw)"""
        try:
            response = (
                self.supabase
                .table('raw_documents')
                .select("*")
                .eq('document_id', document_id)
                .execute()
            )
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
        """Create a new raw document"""
        try:
            response = self.supabase.table('raw_documents').insert(document_data).execute()
            if response.data:
                created = response.data[0]
                self.logger.info(f"Created document with ID: {created.get('document_id')}")
                return created, None
            else:
                msg = "Failed to create document - no data returned"
                self.logger.error(msg)
                return None, msg
        except Exception as e:
            msg = f"Failed to create document: {str(e)}"
            self.logger.error(msg)
            return None, msg

    def update_document(self, document_id: int, document_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Update an existing raw document"""
        try:
            existing, err = self.get_document_by_id(document_id)
            if err:
                return None, err
            if not existing:
                return None, f"Document with ID {document_id} not found"

            resp = (
                self.supabase
                .table('raw_documents')
                .update(document_data)
                .eq('document_id', document_id)
                .execute()
            )
            if resp.data:
                updated = resp.data[0]
                self.logger.info(f"Updated document with ID: {document_id}")
                return updated, None
            else:
                msg = f"Failed to update document {document_id} - no data returned"
                self.logger.error(msg)
                return None, msg
        except Exception as e:
            msg = f"Failed to update document {document_id}: {str(e)}"
            self.logger.error(msg)
            return None, msg

    def delete_document(self, document_id: int) -> tuple[bool, Optional[str]]:
        """Delete a raw document"""
        try:
            existing, err = self.get_document_by_id(document_id)
            if err:
                return False, err
            if not existing:
                return False, f"Document with ID {document_id} not found"

            _ = self.supabase.table('raw_documents').delete().eq('document_id', document_id).execute()
            self.logger.info(f"Deleted document with ID: {document_id}")
            return True, None
        except Exception as e:
            msg = f"Failed to delete document {document_id}: {str(e)}"
            self.logger.error(msg)
            return False, msg

    def search_documents(
        self,
        search_term: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """
        Search processed documents by raw document_name with server-side sort.
        Approach:
          1) Find matching raw document_ids via ilike on raw_documents.
          2) Fetch processed_documents joined rows for those ids.
          3) Apply server-side ordering on the parent by child fields.
        """
        try:
            raw_resp = (
                self.supabase
                .table('raw_documents')
                .select('document_id')
                .ilike('document_name', f'%{search_term}%')
                .execute()
            )
            raw_ids = [r['document_id'] for r in (raw_resp.data or [])]
            if not raw_ids:
                self.logger.info(f"Search for '{search_term}' returned 0 documents")
                return [], None

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

            query = self._apply_sort(query, sort_by, sort_order)

            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment
            if data:
                company_ids = {d['company'] for d in data if d.get('company')}
                company_names: Dict[Any, Any] = {}
                if company_ids:
                    companies = (
                        self.supabase.table('companies')
                        .select('company_id, company_name')
                        .in_('company_id', list(company_ids))
                        .execute()
                    )
                    for c in (companies.data or []):
                        company_names[c['company_id']] = c['company_name']

                for d in data:
                    rd = d.setdefault('raw_documents', {})
                    if d.get('company'):
                        cid = d['company']
                        rd['companies'] = {
                            'company_id': cid,
                            'company_name': company_names.get(cid, 'Unknown Company')
                        }
                    else:
                        rd['companies'] = None

            self.logger.info(f"Search for '{search_term}' returned {len(data)} processed documents")
            return data, None

        except Exception as e:
            msg = f"Failed to search processed documents: {str(e)}"
            self.logger.error(msg)
            return [], msg

    def get_documents_by_status(
        self,
        status: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """Get processed documents by status with server-side sort/pagination."""
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

            query = self._apply_sort(query, sort_by, sort_order)

            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment
            for d in data:
                rd = d.setdefault('raw_documents', {})
                if d.get('company'):
                    rd['companies'] = {'company_id': d['company'], 'company_name': None}
                else:
                    rd['companies'] = None

            self.logger.info(f"Retrieved {len(data)} processed documents with status '{status}'")
            return data, None

        except Exception as e:
            msg = f"Failed to get documents by status: {str(e)}"
            self.logger.error(msg)
            return [], msg

    def get_documents_by_company(
        self,
        company_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """Get processed documents by company with server-side sort/pagination."""
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

            query = self._apply_sort(query, sort_by, sort_order)

            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            for d in data:
                rd = d.setdefault('raw_documents', {})
                rd['companies'] = {'company_id': company_id, 'company_name': None}

            self.logger.info(f"Retrieved {len(data)} processed documents for company {company_id}")
            return data, None

        except Exception as e:
            msg = f"Failed to get documents by company: {str(e)}"
            self.logger.error(msg)
            return [], msg

    def update_document_status(self, document_id: int, status: str) -> tuple[bool, Optional[str]]:
        """Update raw document status"""
        try:
            valid_statuses = ['uploaded', 'processing', 'processed', 'failed']
            if status not in valid_statuses:
                return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

            response = (
                self.supabase
                .table('raw_documents')
                .update({'status': status})
                .eq('document_id', document_id)
                .execute()
            )

            if response.data:
                self.logger.info(f"Updated document {document_id} status to '{status}'")
                return True, None
            else:
                return False, f"Document with ID {document_id} not found"
        except Exception as e:
            msg = f"Failed to update document status: {str(e)}"
            self.logger.error(msg)
            return False, msg

    def create_processed_document(self, document_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Create a processed document with empty tag arrays; optional explanations"""
        try:
            if 'document_id' not in document_data:
                return None, "Missing required field: document_id"

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
            if not response.data:
                return None, "Failed to create processed document - no data returned"

            created = response.data[0]
            process_id = created.get('process_id')
            self.logger.info(f"Created processed document with process_id: {process_id}")

            # Explanations (optional)
            explanations = document_data.get('explanations', [])
            if explanations:
                warn = self.create_explanations(process_id, explanations)
                if warn:
                    self.logger.warning(f"Failed to create explanations: {warn}")

            return created, None

        except Exception as e:
            msg = f"Failed to create processed document: {str(e)}"
            self.logger.error(msg)
            return None, msg

    def update_document_tags(self, document_id: int, tag_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Update processed document tag fields"""
        try:
            existing = (
                self.supabase
                .table('processed_documents')
                .select("*")
                .eq('document_id', document_id)
                .execute()
            )
            if not existing.data:
                return None, f"No processed document found for document_id {document_id}"

            process_id = existing.data[0]['process_id']

            update: Dict[str, Any] = {}
            if 'confirmed_tags' in tag_data:
                if not isinstance(tag_data['confirmed_tags'], list):
                    return None, "confirmed_tags must be an array"
                update['confirmed_tags'] = tag_data['confirmed_tags']

            if 'user_added_labels' in tag_data:
                if not isinstance(tag_data['user_added_labels'], list):
                    return None, "user_added_labels must be an array"
                update['user_added_labels'] = tag_data['user_added_labels']

            if 'user_removed_tags' in tag_data:
                if not isinstance(tag_data['user_removed_tags'], list):
                    return None, "user_removed_tags must be an array"
                update['user_removed_tags'] = tag_data['user_removed_tags']

            update['user_reviewed'] = True
            update['reviewed_at'] = 'now()'
            if 'user_id' in tag_data:
                update['user_id'] = tag_data['user_id']

            if not update:
                return None, "No valid tag data provided for update"

            resp = (
                self.supabase
                .table('processed_documents')
                .update(update)
                .eq('process_id', process_id)
                .execute()
            )
            if not resp.data:
                return None, "Failed to update processed document tags - no data returned"

            updated = resp.data[0]

            # Optional explanations in tag update
            if 'explanations' in tag_data:
                warn = self.create_explanations(process_id, tag_data['explanations'])
                if warn:
                    self.logger.warning(f"Failed to create explanations during tag update: {warn}")

            self.logger.info(f"Updated tags for processed document {process_id} (document_id: {document_id})")
            return updated, None

        except Exception as e:
            msg = f"Failed to update document tags: {str(e)}"
            self.logger.error(msg)
            return None, msg

    def get_unprocessed_documents(self, limit: int = 1) -> tuple[List[Dict], Optional[str]]:
        """Get raw documents that haven't been processed yet (simple client-side diff)"""
        try:
            processed = self.supabase.table('processed_documents').select('document_id').execute()
            processed_ids = {d['document_id'] for d in (processed.data or [])}

            raw = self.supabase.table('raw_documents').select("*").execute()

            unprocessed: List[Dict] = []
            for doc in (raw.data or []):
                if doc['document_id'] not in processed_ids:
                    unprocessed.append(doc)
                    if len(unprocessed) >= limit:
                        break

            self.logger.info(f"Retrieved {len(unprocessed)} unprocessed of {len(raw.data or [])} raw")
            return unprocessed, None

        except Exception as e:
            msg = f"Failed to get unprocessed documents: {str(e)}"
            self.logger.error(msg)
            return [], msg

    # ---------- Explanations ----------

    def create_explanations(self, process_id: int, explanations: List[Dict[str, Any]]) -> Optional[str]:
        """Create explanation rows (best-effort)"""
        try:
            if not explanations:
                return None

            rows = []
            for ex in explanations:
                service_response = ex.get('full_response', {}) or {}
                if ex.get('shap_data'):
                    service_response['shap_explainability'] = ex['shap_data']
                rows.append({
                    'process_id': process_id,
                    'classification_level': ex['level'],
                    'predicted_tag': ex['tag'],
                    'confidence': ex['confidence'],
                    'reasoning': ex.get('reasoning'),
                    'source_service': ex['source'],
                    'service_response': service_response
                })

            resp = self.supabase.table('explanations').insert(rows).execute()
            if resp.data:
                self.logger.info(f"Created {len(resp.data)} explanations for process_id {process_id}")
                return None
            return "Failed to create explanation records - no data returned"

        except Exception as e:
            return f"Failed to create explanations: {str(e)}"

    def get_explanations_for_document(self, document_id: int) -> tuple[List[Dict], Optional[str]]:
        """Get explanations by joining explanations -> processed_documents(document_id)"""
        try:
            resp = (
                self.supabase.table('explanations')
                .select("""
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
                """)
                .eq('processed_documents.document_id', document_id)
                .order('classification_level')
                .execute()
            )
            if not resp.data:
                return [], None

            out: List[Dict] = []
            for item in resp.data:
                flat = {k: v for k, v in item.items() if k != 'processed_documents'}
                flat['document_id'] = item['processed_documents']['document_id']
                out.append(flat)

            self.logger.info(f"Retrieved {len(out)} explanations for document {document_id}")
            return out, None

        except Exception as e:
            return [], f"Failed to get explanations for document {document_id}: {str(e)}"

    # ---------- Sorting helper ----------

    def _apply_sort(self, query, sort_by: Optional[str], sort_order: Optional[str]):
        """
        Apply parent-level ordering by joined raw_documents fields using table(column) syntax.
        Stable tiebreaker on process_id.
        sort_by: "name" | "size" | "date"  (default "name")
        sort_order: "asc" | "desc" (default "asc")
        """
        by = (sort_by or 'name').lower()
        desc = (str(sort_order).lower() == 'desc') if sort_order else False

        if by == 'name':
            primary = "raw_documents(document_name)"
        elif by == 'size':
            primary = "raw_documents(file_size)"
        elif by == 'date':
            primary = "raw_documents(upload_date)"
        else:
            primary = "process_id"

        q = query.order(primary, desc=desc)
        q = q.order('process_id', desc=False)  # stable tiebreaker
        try:
            self.logger.info("Applied sort | primary=%s desc=%s | secondary=process_id.asc", primary, desc)
        except Exception:
            pass
        return q
