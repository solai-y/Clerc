import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SortBy = Optional[str]
SortOrder = Optional[str]

class DatabaseService:
    """Database operations service with error handling + search/sort + robust logging"""
    
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
            self.logger.debug("[DB] test_connection: selecting one from raw_documents")
            _ = self.supabase.table('raw_documents').select("document_id").limit(1).execute()
            self.logger.info("Database connection test successful")
            return True, None
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Database connection test failed: {error_msg}")
            return False, error_msg

    # ----------------------------------------------------------------
    # Unified list/search/sort with robust fallbacks
    # ----------------------------------------------------------------
    def query_documents(
        self,
        *,
        search: Optional[str] = None,
        status: Optional[str] = None,
        company_id: Optional[int] = None,
        sort_by: SortBy = None,          # "name" | "date" | "size"
        sort_order: SortOrder = None,    # "asc" | "desc"
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        primary_tags: Optional[List[str]] = None,
        secondary_tags: Optional[List[str]] = None,
        tertiary_tags: Optional[List[str]] = None
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        List processed_documents joined with raw_documents, applying server-side
        search (by raw_documents.document_name), filters, sorting, and pagination.

        If the DB rejects related-table filter/order, we fall back to Python-side
        filtering/sorting/paging to avoid 500s.
        """
        self.logger.debug(
            "[DB] query_documents params: "
            f"search={search!r}, status={status!r}, company_id={company_id!r}, "
            f"sort_by={sort_by!r}, sort_order={sort_order!r}, limit={limit!r}, offset={offset!r}, "
            f"primary_tags={primary_tags}, secondary_tags={secondary_tags}, tertiary_tags={tertiary_tags}"
        )

        # Join selector: use INNER join if searching on related table so PostgREST can filter
        if search:
            join_selector = """
                *,
                raw_documents!inner(
                    document_name,
                    document_type,
                    link,
                    uploaded_by,
                    upload_date,
                    file_size,
                    file_hash,
                    status
                )
            """
            self.logger.debug("[DB] Using INNER join (search present)")
        else:
            join_selector = """
                *,
                raw_documents(
                    document_name,
                    document_type,
                    link,
                    uploaded_by,
                    upload_date,
                    file_size,
                    file_hash,
                    status
                )
            """
            self.logger.debug("[DB] Using LEFT join (no search)")

        # If tag filters are present, use Python-side filtering (JSONB queries are complex in PostgREST)
        has_tag_filters = (primary_tags and len(primary_tags) > 0) or \
                         (secondary_tags and len(secondary_tags) > 0) or \
                         (tertiary_tags and len(tertiary_tags) > 0)

        if has_tag_filters:
            self.logger.debug("[DB] Tag filters present, using Python-side filtering")
            try:
                # Fetch all documents (or a large window)
                fetch_limit = 1000  # Adjust based on your dataset size
                response = self.supabase.table('processed_documents').select(join_selector).limit(fetch_limit).execute()

                all_rows = response.data or []
                self._attach_company_names_inplace(all_rows)

                # Apply all filters in Python
                filtered = self._filter_in_python(
                    all_rows,
                    search=search,
                    status=status,
                    company_id=company_id,
                    primary_tags=primary_tags,
                    secondary_tags=secondary_tags,
                    tertiary_tags=tertiary_tags
                )
                self.logger.debug(f"[DB] Filtered rows with tags: {len(filtered)}")

                # Sort and paginate
                sorted_rows = self._sort_in_python(filtered, sort_by=sort_by, sort_order=sort_order)
                paged = self._paginate_in_python(sorted_rows, limit=limit, offset=offset)

                self.logger.info(f"Retrieved {len(paged)} processed documents (tag-filtered)")
                return paged, None
            except Exception as e:
                error_msg = f"Failed to query documents with tag filters: {e}"
                self.logger.error(error_msg)
                return [], error_msg

        try:
            query = self.supabase.table('processed_documents').select(join_selector)

            # Filters on processed_documents
            if status:
                query = query.eq('status', status)
            if company_id:
                query = query.eq('company', company_id)

            # Search on related field
            if search:
                like = f"%{search}%"
                query = query.ilike('raw_documents.document_name', like)

            # Server-side sort (use fully qualified column so PostgREST orders on the related table)
            sort_map = {
                'name':  ('document_name',  'raw_documents'),
                'date':  ('upload_date',    'raw_documents'),
                'size':  ('file_size',      'raw_documents'),
            }
            sort_key = (sort_by or 'date').lower()
            col_name, foreign_table = sort_map.get(sort_key, ('upload_date', 'raw_documents'))
            desc = (sort_order or 'desc').lower() == 'desc'
            order_col = f"{foreign_table}.{col_name}"  # e.g. "raw_documents.document_name"
            self.logger.debug(f"[DB] Applying server-side order: {order_col} desc={desc}")
            # IMPORTANT: pass a single fully-qualified column; don't use foreign_table arg (supabase-py ignores it)
            query = query.order(order_col, desc=desc)

            # Pagination
            if offset is not None and limit is not None:
                self.logger.debug(f"[DB] Applying range: start={offset}, end={offset + limit - 1}")
                query = query.range(offset, offset + limit - 1)
            elif limit:
                self.logger.debug(f"[DB] Applying limit: {limit}")
                query = query.limit(limit)

            response = query.execute()
            data = response.data or []
            self.logger.debug(f"[DB] Server-side query returned {len(data)} rows")

            # Attach company names
            self._attach_company_names_inplace(data)

            self.logger.info(f"Retrieved {len(data)} processed documents (server-side)")
            return data, None

        except Exception as e:
            # Fallback path: fetch a window and filter/sort locally to avoid 500s.
            self.logger.warning(f"[DB] Server-side query failed, falling back to Python filter/sort: {e}")

            try:
                fetch_limit = max(limit or 50, 100)
                self.logger.debug(f"[DB] Fallback fetch size: {fetch_limit}")
                response = self.supabase.table('processed_documents').select("""
                    *,
                    raw_documents(
                        document_name,
                        document_type,
                        link,
                        uploaded_by,
                        upload_date,
                        file_size,
                        file_hash,
                        status
                    )
                """).limit(fetch_limit).execute()

                all_rows = response.data or []
                self._attach_company_names_inplace(all_rows)

                filtered = self._filter_in_python(
                    all_rows,
                    search=search,
                    status=status,
                    company_id=company_id,
                    primary_tags=primary_tags,
                    secondary_tags=secondary_tags,
                    tertiary_tags=tertiary_tags
                )
                self.logger.debug(f"[DB] Fallback filtered rows: {len(filtered)}")

                sorted_rows = self._sort_in_python(filtered, sort_by=sort_by, sort_order=sort_order)
                paged = self._paginate_in_python(sorted_rows, limit=limit, offset=offset)

                self.logger.info(f"Retrieved {len(paged)} processed documents (fallback)")
                return paged, None

            except Exception as e2:
                error_msg = f"Failed to query documents (fallback also failed): {e2}"
                self.logger.error(error_msg)
                return [], error_msg
    
    def get_total_documents_count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        company_id: Optional[int] = None,
        primary_tags: Optional[List[str]] = None,
        secondary_tags: Optional[List[str]] = None,
        tertiary_tags: Optional[List[str]] = None
    ) -> tuple[int, Optional[str]]:
        """Get total count of processed documents with optional filters (matches query_documents)."""
        self.logger.debug(
            "[DB] get_total_documents_count params: "
            f"search={search!r}, status={status!r}, company_id={company_id!r}, "
            f"primary_tags={primary_tags}, secondary_tags={secondary_tags}, tertiary_tags={tertiary_tags}"
        )
        # If tag filters are present, use Python-side counting
        has_tag_filters = (primary_tags and len(primary_tags) > 0) or \
                         (secondary_tags and len(secondary_tags) > 0) or \
                         (tertiary_tags and len(tertiary_tags) > 0)

        if has_tag_filters:
            self.logger.debug("[DB] Tag filters present in count, using Python-side counting")
            try:
                response = self.supabase.table('processed_documents').select("""
                    *,
                    raw_documents(
                        document_name,
                        document_type,
                        link,
                        uploaded_by,
                        upload_date,
                        file_size,
                        file_hash,
                        status
                    )
                """).limit(1000).execute()
                rows = response.data or []
                filtered = self._filter_in_python(
                    rows,
                    search=search,
                    status=status,
                    company_id=company_id,
                    primary_tags=primary_tags,
                    secondary_tags=secondary_tags,
                    tertiary_tags=tertiary_tags
                )
                count = len(filtered)
                self.logger.info(f"Total processed documents count (tag-filtered): {count}")
                return count, None
            except Exception as e:
                error_msg = f"Failed to get processed documents count with tag filters: {str(e)}"
                self.logger.error(error_msg)
                return 0, error_msg

        try:
            # If searching on related field, use inner join in select so ilike works
            if search:
                select_expr = "process_id, raw_documents!inner(document_name)"
            else:
                select_expr = "process_id"

            query = self.supabase.table('processed_documents').select(select_expr, count="exact")

            if status:
                query = query.eq('status', status)
            if company_id:
                query = query.eq('company', company_id)
            if search:
                query = query.ilike('raw_documents.document_name', f'%{search}%')

            response = query.execute()
            total_count = response.count if response.count is not None else 0
            self.logger.info(f"Total processed documents count: {total_count} (server-side)")
            return total_count, None
        except Exception as e:
            self.logger.warning(f"[DB] Count query failed, falling back to Python count: {e}")
            try:
                # Pull a biggish slice and count locally (tests typically small).
                response = self.supabase.table('processed_documents').select("""
                    *,
                    raw_documents(
                        document_name,
                        document_type,
                        link,
                        uploaded_by,
                        upload_date,
                        file_size,
                        file_hash,
                        status
                    )
                """).limit(1000).execute()
                rows = response.data or []
                filtered = self._filter_in_python(
                    rows,
                    search=search,
                    status=status,
                    company_id=company_id,
                    primary_tags=primary_tags,
                    secondary_tags=secondary_tags,
                    tertiary_tags=tertiary_tags
                )
                count = len(filtered)
                self.logger.info(f"Total processed documents count (fallback): {count}")
                return count, None
            except Exception as e2:
                error_msg = f"Failed to get processed documents count: {str(e2)}"
                self.logger.error(error_msg)
                return 0, error_msg

    # ---------------- Existing single-item endpoints ----------------

    def get_all_documents(self, limit: Optional[int] = None, offset: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get all processed documents with document info from raw_documents (delegates to query_documents)."""
        return self.query_documents(limit=limit, offset=offset)

    def get_document_by_id(self, document_id: int) -> tuple[Optional[Dict], Optional[str]]:
        """Get document by ID"""
        try:
            self.logger.debug(f"[DB] get_document_by_id: {document_id}")
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
            self.logger.debug(f"[DB] create_document keys: {list(document_data.keys())}")
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
            self.logger.debug(f"[DB] update_document id={document_id} keys={list(document_data.keys())}")
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
            self.logger.debug(f"[DB] delete_document id={document_id}")
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
    
    def search_documents(self, search_term: str, limit: Optional[int] = None, offset: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Search processed documents by document name (delegates to query_documents)."""
        return self.query_documents(search=search_term, limit=limit, offset=offset)
    
    def get_documents_by_status(self, status: str, limit: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get documents by status (delegates to query_documents)."""
        return self.query_documents(status=status, limit=limit)
    
    def get_documents_by_company(self, company_id: int, limit: Optional[int] = None) -> tuple[List[Dict], Optional[str]]:
        """Get processed documents by company ID (delegates to query_documents)."""
        return self.query_documents(company_id=company_id, limit=limit)
    
    def update_document_status(self, document_id: int, status: str) -> tuple[bool, Optional[str]]:
        """Update document status"""
        try:
            valid_statuses = ['uploaded', 'processing', 'processed', 'failed', 'api_processed']
            if status not in valid_statuses:
                return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            
            self.logger.debug(f"[DB] update_document_status id={document_id} -> {status}")
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

    # ----------------------------------------------------------------
    # Helpers (attach company, filter/sort/paginate fallback)
    # ----------------------------------------------------------------
    def _attach_company_names_inplace(self, rows: List[Dict]) -> None:
        """Attach companies object into row['raw_documents']['companies'] based on processed_documents.company."""
        try:
            company_ids = {r['company'] for r in rows if r.get('company')}
            if not company_ids:
                return
            companies_response = self.supabase.table('companies').select('company_id, company_name').in_('company_id', list(company_ids)).execute()
            mapping = {c['company_id']: c['company_name'] for c in (companies_response.data or [])}
            for r in rows:
                if 'raw_documents' in r and isinstance(r['raw_documents'], dict):
                    if r.get('company'):
                        cid = r['company']
                        r['raw_documents']['companies'] = {
                            'company_id': cid,
                            'company_name': mapping.get(cid, 'Unknown Company')
                        }
                    else:
                        r['raw_documents']['companies'] = None
        except Exception as e:
            self.logger.warning(f"[DB] _attach_company_names_inplace failed (non-fatal): {e}")

    def _filter_in_python(
        self,
        rows: List[Dict],
        *,
        search: Optional[str],
        status: Optional[str],
        company_id: Optional[int],
        primary_tags: Optional[List[str]] = None,
        secondary_tags: Optional[List[str]] = None,
        tertiary_tags: Optional[List[str]] = None
    ) -> List[Dict]:
        term = (search or "").strip().lower()
        out: List[Dict] = []
        for r in rows:
            if status and r.get('status') != status:
                continue
            if company_id and r.get('company') != company_id:
                continue
            if term:
                try:
                    name = (r.get('raw_documents') or {}).get('document_name') or ""
                except Exception:
                    name = ""
                if term not in name.lower():
                    continue

            # Tag filtering: extract tags from confirmed_tags JSONB structure
            if primary_tags or secondary_tags or tertiary_tags:
                confirmed = r.get('confirmed_tags', {})

                # Handle nested structure: confirmed_tags.confirmed_tags.tags[]
                if isinstance(confirmed, dict):
                    tags_list = confirmed.get('confirmed_tags', {}).get('tags', [])
                else:
                    tags_list = []

                # Skip documents with no tags
                if not tags_list:
                    continue

                # Extract tags by level
                doc_primary = {t['tag'] for t in tags_list if t.get('level') == 'primary'}
                doc_secondary = {t['tag'] for t in tags_list if t.get('level') == 'secondary'}
                doc_tertiary = {t['tag'] for t in tags_list if t.get('level') == 'tertiary'}

                # OR logic within each tier, AND logic across tiers
                if primary_tags and len(primary_tags) > 0:
                    if not any(tag in doc_primary for tag in primary_tags):
                        continue

                if secondary_tags and len(secondary_tags) > 0:
                    if not any(tag in doc_secondary for tag in secondary_tags):
                        continue

                if tertiary_tags and len(tertiary_tags) > 0:
                    if not any(tag in doc_tertiary for tag in tertiary_tags):
                        continue

            out.append(r)
        return out

    def _sort_in_python(
        self,
        rows: List[Dict],
        *,
        sort_by: SortBy,
        sort_order: SortOrder
    ) -> List[Dict]:
        key = (sort_by or 'date').lower()
        reverse = (sort_order or 'desc').lower() == 'desc'

        def safe_get(d: Dict, path: List[str], default=None):
            cur = d
            try:
                for p in path:
                    cur = cur.get(p) if isinstance(cur, dict) else None
                return cur if cur is not None else default
            except Exception:
                return default

        if key == 'name':
            rows.sort(key=lambda r: (safe_get(r, ['raw_documents', 'document_name'], "") or "").lower(), reverse=reverse)
        elif key == 'size':
            rows.sort(key=lambda r: safe_get(r, ['raw_documents', 'file_size'], -1) or -1, reverse=reverse)
        else:  # 'date'
            rows.sort(key=lambda r: safe_get(r, ['raw_documents', 'upload_date'], "") or "", reverse=reverse)
        return rows

    def _paginate_in_python(self, rows: List[Dict], *, limit: Optional[int], offset: Optional[int]) -> List[Dict]:
        if limit is None and offset is None:
            return rows
        start = offset or 0
        end = start + (limit or len(rows))
        return rows[start:end]

    # ----------------------------------------------------------------
    # The rest of your existing methods unchanged (processed creation, tags, explanations, etc.)
    # ----------------------------------------------------------------
    
    def create_processed_document(self, document_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Create a new processed document entry with empty tag fields and explanations"""
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
                'confirmed_tags': [],  # Empty array (or JSONB in your schema)
                'user_added_labels': [],  # Empty array
                'user_removed_tags': [],  # Empty array
                'user_reviewed': False,
                'user_id': document_data.get('user_id'),
                'company': document_data.get('company'),  # Optional company field
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
                
                # Create explanations if provided
                explanations = document_data.get('explanations', [])
                if explanations:
                    self.logger.info(f"Creating explanations for process_id {process_id}: {len(explanations)}")
                    explanation_error = self.create_explanations(process_id, explanations)
                    if explanation_error:
                        self.logger.warning(f"Failed to create explanations for process_id {process_id}: {explanation_error}")
                    else:
                        self.logger.info(f"Successfully created explanations for process_id {process_id}")
                
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
                confirmed_tags = tag_data['confirmed_tags']
                if isinstance(confirmed_tags, list):
                    # Legacy -> wrap to JSONB-ish structure
                    update_data['confirmed_tags'] = {
                        "tags": [
                            {
                                "tag": tag,
                                "source": "legacy",
                                "confidence": 1.0,
                                "confirmed": True,
                                "added_by": "migrated",
                                "added_at": "now()",
                                "level": "unknown"
                            } for tag in confirmed_tags
                        ]
                    }
                elif isinstance(confirmed_tags, dict):
                    update_data['confirmed_tags'] = confirmed_tags
                else:
                    return None, "confirmed_tags must be an array or object"
            
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
                    self.logger.info(f"Creating explanations during tag update for process_id {process_id}: {len(tag_data['explanations'])} explanations")
                    explanation_error = self.create_explanations(process_id, tag_data['explanations'])
                    if explanation_error:
                        self.logger.warning(f"Failed to create explanations during tag update for process_id {process_id}: {explanation_error}")
                    else:
                        self.logger.info(f"Successfully created explanations during tag update for process_id {process_id}")

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
            processed_ids = {doc['document_id'] for doc in processed_response.data}
            
            raw_response = self.supabase.table('raw_documents').select("*").execute()
            
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
    
    def create_explanations(self, process_id: int, explanations: List[Dict[str, Any]]) -> Optional[str]:
        """Create explanation records for a processed document"""
        try:
            explanation_records = []
            for explanation in explanations:
                level = explanation.get('level')
                tag = explanation.get('tag')
                confidence = explanation.get('confidence')
                source = explanation.get('source')

                if not all([level, tag, confidence is not None, source]):
                    self.logger.warning(f"Skipping explanation with missing required fields: {explanation}")
                    continue

                if level not in ['primary', 'secondary', 'tertiary']:
                    self.logger.warning(f"Invalid classification_level '{level}', skipping explanation")
                    continue

                valid_sources = ['ai', 'llm', 'ai_override']
                if source not in valid_sources:
                    self.logger.warning(f"Invalid source_service '{source}', skipping explanation")
                    continue

                try:
                    confidence_float = float(confidence)
                    if confidence_float < 0.0 or confidence_float > 1.0:
                        self.logger.warning(f"Confidence {confidence_float} out of range [0,1], skipping explanation")
                        continue
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid confidence value '{confidence}', skipping explanation")
                    continue

                service_response = explanation.get('full_response', {})
                if explanation.get('shap_data'):
                    service_response['shap_explainability'] = explanation['shap_data']

                record = {
                    'process_id': process_id,
                    'classification_level': level,
                    'predicted_tag': str(tag),
                    'confidence': confidence_float,
                    'reasoning': explanation.get('reasoning'),
                    'source_service': source,
                    'service_response': service_response
                }
                explanation_records.append(record)

            if explanation_records:
                self.logger.info(f"Attempting to insert {len(explanation_records)} explanation records for process_id {process_id}")

                explanation_groups: Dict[str, Dict[str, Dict[str, Any]]] = {}
                for record in explanation_records:
                    level = record['classification_level']
                    source = record['source_service']
                    if level not in explanation_groups:
                        explanation_groups[level] = {}
                    explanation_groups[level][source] = record

                successful_inserts = 0
                failed_inserts = 0

                for level, sources in explanation_groups.items():
                    if 'llm' in sources and 'ai' in sources:
                        llm_record = sources['llm']
                        ai_record = sources['ai'].copy()
                        ai_record['source_service'] = 'ai_override'
                        ai_record['reasoning'] = f"AI prediction (overridden by LLM): {ai_record.get('reasoning')}"
                        records_to_insert = [llm_record, ai_record]
                    elif 'llm' in sources:
                        records_to_insert = [sources['llm']]
                    elif 'ai' in sources:
                        records_to_insert = [sources['ai']]
                    else:
                        records_to_insert = []

                    for rec in records_to_insert:
                        try:
                            response = self.supabase.table('explanations').insert([rec]).execute()
                            if response.data:
                                successful_inserts += 1
                                self.logger.info(f"Inserted {rec['source_service']} explanation for {level}")
                            else:
                                failed_inserts += 1
                                self.logger.warning(f"Failed to insert {rec['source_service']} explanation for {level}")
                        except Exception as insert_error:
                            if "duplicate key value violates unique constraint" in str(insert_error):
                                self.logger.warning(f"Skipping duplicate explanation for {level} ({rec['source_service']})")
                                failed_inserts += 1
                            else:
                                self.logger.warning(f"Failed to insert {rec['source_service']} explanation for {level}: {insert_error}")
                                failed_inserts += 1

                if successful_inserts > 0:
                    self.logger.info(f"Successfully created {successful_inserts} explanation records for process_id {process_id}")
                    if failed_inserts > 0:
                        self.logger.warning(f"{failed_inserts} explanation records failed to insert for process_id {process_id}")
                    return None
                else:
                    error_msg = f"Failed to create any explanation records for process_id {process_id}"
                    self.logger.error(error_msg)
                    return error_msg
            else:
                self.logger.warning(f"No valid explanation records to insert for process_id {process_id}")
                return None

        except Exception as e:
            error_msg = f"Failed to create explanations: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Explanation data that caused error: {explanations}")
            return error_msg
    
    def get_complete_document_by_id(self, document_id: int) -> tuple[Optional[Dict], Optional[str]]:
        """Get complete document information including both raw and processed data"""
        try:
            response = self.supabase.table('processed_documents').select("""
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
            """).eq('document_id', document_id).execute()

            if response.data:
                document = response.data[0]
                if document.get('raw_documents'):
                    raw_data = document['raw_documents']
                    document.update(raw_data)
                    del document['raw_documents']

                self.logger.info(f"Retrieved complete document with ID: {document_id}")
                return document, None
            else:
                raw_response = self.supabase.table('raw_documents').select("*").eq('document_id', document_id).execute()
                if raw_response.data:
                    self.logger.info(f"Retrieved raw document only with ID: {document_id}")
                    return raw_response.data[0], None
                else:
                    self.logger.warning(f"Document with ID {document_id} not found")
                    return None, f"Document with ID {document_id} not found"

        except Exception as e:
            error_msg = f"Failed to retrieve complete document: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg

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
