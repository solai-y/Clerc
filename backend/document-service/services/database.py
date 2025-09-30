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
            # Build base query for counting processed documents
            query = self.supabase.table('processed_documents').select("process_id", count="exact")
            
            # Apply filters
            if status:
                query = query.eq('status', status)
            
            if company_id:
                query = query.eq('company', company_id)  # Company is now in processed_documents
            
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
            
            # Fetch company names for processed documents that have company IDs
            if response.data:
                # Get unique company IDs from processed_documents.company (not raw_documents)
                company_ids = set()
                for doc in response.data:
                    if doc.get('company'):
                        company_ids.add(doc['company'])
                
                # Fetch company information if we have company IDs
                company_names = {}
                if company_ids:
                    companies_response = self.supabase.table('companies').select('company_id, company_name').in_('company_id', list(company_ids)).execute()
                    for company in companies_response.data:
                        company_names[company['company_id']] = company['company_name']
                
                # Add company names to the documents
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
        """Get processed documents by company ID (company is now in processed_documents)"""
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
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            self.logger.info(f"Retrieved {len(response.data)} processed documents for company {company_id}")
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
                'confirmed_tags': [],  # Empty array
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
                    self.logger.info(f"Creating explanations for process_id {process_id}: {len(explanations)} explanations")
                    explanation_error = self.create_explanations(process_id, explanations)
                    if explanation_error:
                        self.logger.warning(f"Failed to create explanations for process_id {process_id}: {explanation_error}")
                        # Don't fail the whole operation, just log the warning - document creation should continue
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
            # First check if processed document exists for this document_id
            existing_response = self.supabase.table('processed_documents').select("*").eq('document_id', document_id).execute()
            
            if not existing_response.data:
                return None, f"No processed document found for document_id {document_id}"
            
            existing_doc = existing_response.data[0]
            process_id = existing_doc['process_id']
            
            # Prepare update data
            update_data = {}
            
            if 'confirmed_tags' in tag_data:
                # Handle both legacy array format and new JSONB format
                confirmed_tags = tag_data['confirmed_tags']
                if isinstance(confirmed_tags, list):
                    # Legacy format - convert to new JSONB format
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
                    # New JSONB format - use as is
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

                # Handle explanations if provided
                if 'explanations' in tag_data:
                    self.logger.info(f"Creating explanations during tag update for process_id {process_id}: {len(tag_data['explanations'])} explanations")
                    explanation_error = self.create_explanations(process_id, tag_data['explanations'])
                    if explanation_error:
                        self.logger.warning(f"Failed to create explanations during tag update for process_id {process_id}: {explanation_error}")
                        # Don't fail the whole operation, just log the warning - tag update should continue
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
    
    def create_explanations(self, process_id: int, explanations: List[Dict[str, Any]]) -> Optional[str]:
        """Create explanation records for a processed document"""
        try:
            explanation_records = []
            for explanation in explanations:
                # Validate required fields
                level = explanation.get('level')
                tag = explanation.get('tag')
                confidence = explanation.get('confidence')
                source = explanation.get('source')

                # Skip explanations with missing required fields
                if not all([level, tag, confidence is not None, source]):
                    self.logger.warning(f"Skipping explanation with missing required fields: {explanation}")
                    continue

                # Validate classification_level constraint
                if level not in ['primary', 'secondary', 'tertiary']:
                    self.logger.warning(f"Invalid classification_level '{level}', skipping explanation")
                    continue

                # Validate source_service constraint (allow ai_override for duplicate handling)
                valid_sources = ['ai', 'llm', 'ai_override']
                if source not in valid_sources:
                    self.logger.warning(f"Invalid source_service '{source}', skipping explanation")
                    continue

                # Validate confidence range
                try:
                    confidence_float = float(confidence)
                    if confidence_float < 0.0 or confidence_float > 1.0:
                        self.logger.warning(f"Confidence {confidence_float} out of range [0,1], skipping explanation")
                        continue
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid confidence value '{confidence}', skipping explanation")
                    continue

                # Build service response with SHAP data if available
                service_response = explanation.get('full_response', {})
                if explanation.get('shap_data'):
                    service_response['shap_explainability'] = explanation['shap_data']

                record = {
                    'process_id': process_id,
                    'classification_level': level,
                    'predicted_tag': str(tag),  # Ensure string type
                    'confidence': confidence_float,
                    'reasoning': explanation.get('reasoning'),
                    'source_service': source,
                    'service_response': service_response
                }
                explanation_records.append(record)

            if explanation_records:
                self.logger.info(f"Attempting to insert {len(explanation_records)} explanation records for process_id {process_id}")

                # Group explanations by level to handle duplicates properly
                explanation_groups = {}
                for record in explanation_records:
                    level = record['classification_level']
                    source = record['source_service']
                    key = f"{level}_{source}"

                    if level not in explanation_groups:
                        explanation_groups[level] = {}
                    explanation_groups[level][source] = record

                # Insert explanations, preferring LLM over AI for each level
                successful_inserts = 0
                failed_inserts = 0

                for level, sources in explanation_groups.items():
                    # Determine which explanation to store for this level
                    if 'llm' in sources and 'ai' in sources:
                        # Store LLM as primary, AI with modified source to avoid constraint
                        llm_record = sources['llm']
                        ai_record = sources['ai'].copy()
                        ai_record['source_service'] = 'ai_override'  # Modify to avoid unique constraint
                        ai_record['reasoning'] = f"AI prediction (overridden by LLM): {ai_record['reasoning']}"

                        records_to_insert = [llm_record, ai_record]
                    elif 'llm' in sources:
                        records_to_insert = [sources['llm']]
                    elif 'ai' in sources:
                        records_to_insert = [sources['ai']]
                    else:
                        continue

                    # Insert the records for this level
                    for record in records_to_insert:
                        try:
                            response = self.supabase.table('explanations').insert([record]).execute()
                            if response.data:
                                successful_inserts += 1
                                self.logger.info(f"Inserted {record['source_service']} explanation for {level}")
                            else:
                                failed_inserts += 1
                                self.logger.warning(f"Failed to insert {record['source_service']} explanation for {level}")
                        except Exception as insert_error:
                            error_str = str(insert_error)
                            if "duplicate key value violates unique constraint" in error_str:
                                self.logger.warning(f"Skipping duplicate explanation for {level} ({record['source_service']})")
                                failed_inserts += 1
                            else:
                                self.logger.warning(f"Failed to insert {record['source_service']} explanation for {level}: {error_str}")
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
            # Query processed_documents and join with raw_documents
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
                # Get the first (should be only) result
                document = response.data[0]

                # Flatten the structure for easier access
                if document.get('raw_documents'):
                    raw_data = document['raw_documents']
                    document.update(raw_data)
                    del document['raw_documents']

                self.logger.info(f"Retrieved complete document with ID: {document_id}")
                return document, None
            else:
                # Fallback to raw_documents only if no processed document exists
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
            # Join explanations with processed_documents to get explanations by document_id
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
                # Flatten the response to remove nested processed_documents
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