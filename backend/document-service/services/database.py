import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class DatabaseService:
    """Database operations service with error handling"""

    # Your requested fallback test user UUID (must match access_control.user)
    FALLBACK_UPLOADED_BY_ID = "49991737-c3c2-4916-b2e8-03a23c9cd36a"

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
        Be defensive: avoid count='exact' in queries that have caused upstream errors.
        """
        try:
            if search:
                # Find matching raw doc IDs (count locally to avoid worker errors)
                raw_resp = (
                    self.supabase
                    .table('raw_documents')
                    .select('document_id')        # no count='exact' here
                    .ilike('document_name', f'%{search}%')
                    .execute()
                )
                raw_ids = [r['document_id'] for r in (raw_resp.data or [])]
                if not raw_ids:
                    return 0, None

                # Count processed rows locally
                proc_resp = (
                    self.supabase
                    .table('processed_documents')
                    .select('process_id')
                    .in_('document_id', raw_ids)
                    .execute()
                )
                proc_rows = proc_resp.data or []
                if status:
                    proc_rows = [r for r in proc_rows if r.get('status') == status]
                if company_id:
                    proc_rows = [r for r in proc_rows if r.get('company') == company_id]
                return len(proc_rows), None

            # No search: lightweight count via select+len
            query = self.supabase.table('processed_documents').select('process_id')
            if status:
                query = query.eq('status', status)
            if company_id:
                query = query.eq('company', company_id)
            resp = query.execute()
            return len(resp.data or []), None

        except Exception as e:
            # Be resilient: return 0 rather than failing the whole endpoint
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

            query = self._apply_sort(query, sort_by, sort_order)

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
                company_ids = {doc['company'] for doc in response.data if doc.get('company')}
                company_names: Dict[Any, Any] = {}
                if company_ids:
                    companies_response = (
                        self.supabase
                        .table('companies')
                        .select('company_id, company_name')
                        .in_('company_id', list(company_ids)).execute()
                    )
                    for c in (companies_response.data or []):
                        company_names[c['company_id']] = c['company_name']

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
            # Resolve uploaded_by to a real FK (or fallback)
            if 'uploaded_by' in document_data:
                resolved_id, resolve_err = self._resolve_uploaded_by(document_data.get('uploaded_by'))
                if resolve_err:
                    return None, resolve_err
                document_data['uploaded_by'] = resolved_id
            else:
                resolved_id, resolve_err = self._resolve_uploaded_by(None)
                if resolve_err:
                    return None, resolve_err
                document_data['uploaded_by'] = resolved_id

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

            if 'uploaded_by' in document_data:
                resolved_id, resolve_err = self._resolve_uploaded_by(document_data.get('uploaded_by'))
                if resolve_err:
                    return None, resolve_err
                document_data['uploaded_by'] = resolved_id

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
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str]]:
        """Search processed documents by raw document_name, with correct pagination order."""
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
            elif limit is not None:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment
            if data:
                company_ids = {doc['company'] for doc in data if doc.get('company')}
                company_names: Dict[Any, Any] = {}
                if company_ids:
                    companies_response = (
                        self.supabase
                        .table('companies')
                        .select('company_id, company_name')
                        .in_('company_id', list(company_ids))
                        .execute()
                    )
                    for c in (companies_response.data or []):
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

            query = self._apply_sort(query, sort_by, sort_order)

            if offset is not None and limit is not None:
                query = query.range(offset, offset + limit - 1)
            elif limit:
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []

            # Company enrichment
            if data:
                company_ids = {doc['company'] for doc in data if doc.get('company')}
                company_names: Dict[Any, Any] = {}
                if company_ids:
                    companies_response = (
                        self.supabase
                        .table('companies')
                        .select('company_id, company_name')
                        .in_('company_id', list(company_ids))
                        .execute()
                    )
                    for c in (companies_response.data or []):
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

            query = self._apply_sort(query, sort_by, sort_order)

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

    # ---------- Helpers ----------

    def _resolve_uploaded_by(self, uploaded_by: Any) -> Tuple[Optional[Any], Optional[str]]:
        """
        Ensure uploaded_by points to a real access_control.user (UUID).
        Priority:
          1) If the provided id exists (in access_control.user), keep it.
          2) Else if FALLBACK_UPLOADED_BY_ID exists, use it.
          3) Else use the first available user in access_control.
          4) If no users exist, return an error.
        """
        try:
            # 1) If caller provided an id and it exists, use it as-is
            if uploaded_by is not None:
                check = (
                    self.supabase.table('access_control')
                    .select('user')                 # <-- correct column name
                    .eq('user', uploaded_by)
                    .limit(1)
                    .execute()
                )
                if check.data:
                    return uploaded_by, None

            # 2) Try the configured fallback UUID
            fb = self.FALLBACK_UPLOADED_BY_ID
            fb_check = (
                self.supabase.table('access_control')
                .select('user')
                .eq('user', fb)
                .limit(1)
                .execute()
            )
            if fb_check.data:
                if uploaded_by is not None and uploaded_by != fb:
                    self.logger.warning(
                        "uploaded_by=%s not found; remapping to fallback user=%s",
                        uploaded_by, fb
                    )
                return fb, None

            # 3) Fall back to any existing user (pick first)
            any_user = (
                self.supabase.table('access_control')
                .select('user')
                .order('user', desc=False)   # deterministic pick
                .limit(1)
                .execute()
            )
            if any_user.data:
                fallback_id = any_user.data[0]['user']
                self.logger.warning(
                    "uploaded_by=%s not found; fallback %s not present either; "
                    "remapping to existing user=%s",
                    uploaded_by, fb, fallback_id
                )
                return fallback_id, None

            # 4) No users at all – surface a clear error
            return None, (
                "Failed to resolve uploaded_by: no rows in access_control "
                f"(tried provided='{uploaded_by}' and fallback='{fb}')"
            )

        except Exception as e:
            msg = f"Failed to resolve uploaded_by: {str(e)}"
            self.logger.error(msg)
            return None, msg

    def _apply_sort(self, query, sort_by: str | None, sort_order: str | None):
        """
        Apply parent-level ordering by related raw_documents fields using table(column) syntax.
        This sorts the parent processed_documents rows by the child column, not just the embedded array.
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
