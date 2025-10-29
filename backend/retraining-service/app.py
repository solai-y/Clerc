"""
Retraining Service - Stores document text and confirmed tags for model retraining
Built with FastAPI
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration using Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")

supabase: Client = create_client(supabase_url, supabase_key)

# Pydantic models
class StoreTextRequest(BaseModel):
    document_id: int = Field(..., description="Document ID from raw_documents table")
    text: str = Field(..., description="Extracted document text")

class TagInfo(BaseModel):
    tag: str
    level: str
    source: Optional[str] = None
    confidence: Optional[float] = None

class ConfirmedTags(BaseModel):
    tags: List[TagInfo]

class UpdateTagsRequest(BaseModel):
    document_id: int = Field(..., description="Document ID")
    confirmed_tags: ConfirmedTags = Field(..., description="Confirmed tag hierarchies")

class TagHierarchyDetail(BaseModel):
    id: Optional[int]
    name: Optional[str]

class RetrainingDataRow(BaseModel):
    id: int
    document_id: int
    text_preview: str
    text_length: int
    primary_tags: List[TagHierarchyDetail]
    secondary_tags: List[TagHierarchyDetail]
    tertiary_tags: List[TagHierarchyDetail]
    created_at: Optional[str]
    updated_at: Optional[str]

class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

def get_tag_id_by_name(tag_name: str) -> Optional[int]:
    """Look up tag ID by tag name using Supabase"""
    try:
        response = supabase.table('tags').select('id').eq('tag_name', tag_name).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        return None
    except Exception as e:
        logger.error(f"Failed to look up tag '{tag_name}': {str(e)}")
        return None

# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Retraining Service...")

    # Test database connection
    try:
        response = supabase.table('retraining_data').select("id").limit(1).execute()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")

    yield

    logger.info("Shutting down Retraining Service...")

app = FastAPI(
    title="Retraining Service",
    description="Stores document text and confirmed tags for AI model retraining",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        'service': 'Retraining Service',
        'status': 'healthy',
        'version': '1.0.0',
        'description': 'Stores document text and confirmed tags for model retraining'
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        response = supabase.table('retraining_data').select("id").limit(1).execute()
        return {
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }
        )

@app.post("/retraining/store-text", response_model=APIResponse)
async def store_document_text(request: StoreTextRequest):
    """
    Store document text for retraining (called after text extraction)
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="text is required")

        # Insert initial row with document_id and text, tags will be null
        response = supabase.table('retraining_data').insert({
            'document_id': request.document_id,
            'document_text': request.text
        }).execute()

        if response.data and len(response.data) > 0:
            result = response.data[0]
            logger.info(f"Stored retraining text for document {request.document_id}, row ID: {result['id']}")

            return APIResponse(
                status="success",
                message="Document text stored for retraining",
                data={
                    'retraining_id': result['id'],
                    'document_id': result['document_id'],
                    'text_length': len(request.text),
                    'created_at': result.get('created_at')
                }
            )
        else:
            logger.error("Failed to store document text - no data returned")
            raise HTTPException(
                status_code=500,
                detail='Failed to store document text'
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store document text: {str(e)}")
        if "foreign key" in str(e).lower() or "violates" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail='Database integrity error - Document may not exist in raw_documents'
            )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/retraining/update-tags", response_model=APIResponse)
async def update_tags(request: UpdateTagsRequest):
    """
    Update retraining data with confirmed tags (called after tag confirmation)

    Stores multiple tags per level as arrays - no hierarchy building required.
    """
    try:
        logger.info(f"Received update-tags request for document_id: {request.document_id}")
        logger.info(f"Confirmed tags: {[{'tag': t.tag, 'level': t.level} for t in request.confirmed_tags.tags]}")

        if not request.confirmed_tags.tags:
            raise HTTPException(status_code=400, detail="confirmed_tags.tags array is required")

        # First, get the document text from existing rows
        logger.info(f"Querying retraining_data for document_id: {request.document_id}")
        response = supabase.table('retraining_data').select('document_text').eq('document_id', request.document_id).limit(1).execute()
        logger.info(f"Query result: found {len(response.data) if response.data else 0} rows")

        if not response.data or len(response.data) == 0:
            logger.warning(f"No existing retraining data found for document {request.document_id}, will create new entry")
            raise HTTPException(
                status_code=404,
                detail=f'Document text not found for document_id {request.document_id} - Must call /store-text before updating tags'
            )

        document_text = response.data[0]['document_text']
        logger.info(f"Found existing retraining data for document {request.document_id}, text length: {len(document_text)}")

        # Group tags by level
        tags_list = request.confirmed_tags.tags
        primary_tags = [t for t in tags_list if t.level == 'primary']
        secondary_tags = [t for t in tags_list if t.level == 'secondary']
        tertiary_tags = [t for t in tags_list if t.level == 'tertiary']

        logger.info(f"Processing {len(primary_tags)} primary, {len(secondary_tags)} secondary, {len(tertiary_tags)} tertiary tags")

        # Look up all tag IDs with fuzzy matching (handle spaces, underscores, case differences)
        all_tag_names = [t.tag for t in tags_list]
        tag_lookup = {}

        if all_tag_names:
            # First try exact match
            tags_response = supabase.table('tags').select('id, tag_name').in_('tag_name', all_tag_names).execute()
            if tags_response.data:
                tag_lookup = {tag['tag_name']: tag['id'] for tag in tags_response.data}

            # For any tags that didn't match, try fuzzy matching
            unmatched_tags = [name for name in all_tag_names if name not in tag_lookup]
            if unmatched_tags:
                # Fetch all tags and do case-insensitive matching with normalization
                all_tags_response = supabase.table('tags').select('id, tag_name').execute()
                if all_tags_response.data:
                    # Create normalized lookup
                    def normalize(s):
                        return s.lower().replace('_', ' ').replace('-', ' ').strip()

                    db_tags_normalized = {
                        normalize(tag['tag_name']): tag
                        for tag in all_tags_response.data
                    }

                    # Try to match unmatched tags
                    for unmatched in unmatched_tags:
                        normalized_unmatched = normalize(unmatched)
                        if normalized_unmatched in db_tags_normalized:
                            matched_tag = db_tags_normalized[normalized_unmatched]
                            tag_lookup[unmatched] = matched_tag['id']
                            logger.info(f"Fuzzy matched '{unmatched}' to '{matched_tag['tag_name']}' (id={matched_tag['id']})")
                        else:
                            logger.warning(f"Could not find tag '{unmatched}' even with fuzzy matching")

        # Build tag ID arrays for each level
        primary_tag_ids = []
        secondary_tag_ids = []
        tertiary_tag_ids = []

        for tag in primary_tags:
            tag_id = tag_lookup.get(tag.tag)
            if tag_id:
                primary_tag_ids.append(tag_id)
            else:
                logger.warning(f"Primary tag '{tag.tag}' not found in tags table")

        for tag in secondary_tags:
            tag_id = tag_lookup.get(tag.tag)
            if tag_id:
                secondary_tag_ids.append(tag_id)
            else:
                logger.warning(f"Secondary tag '{tag.tag}' not found in tags table")

        for tag in tertiary_tags:
            tag_id = tag_lookup.get(tag.tag)
            if tag_id:
                tertiary_tag_ids.append(tag_id)
            else:
                logger.warning(f"Tertiary tag '{tag.tag}' not found in tags table")

        # Check if we found any valid tags
        if not primary_tag_ids and not secondary_tag_ids and not tertiary_tag_ids:
            logger.warning(f"No tags found in database for document {request.document_id}")
            raise HTTPException(
                status_code=400,
                detail='No valid tags found in database - Make sure confirmed tags exist in the tags table'
            )

        # Delete old rows for this document
        supabase.table('retraining_data').delete().eq('document_id', request.document_id).execute()
        logger.info(f"Deleted old retraining rows for document {request.document_id}")

        # Insert single row with tag arrays
        insert_response = supabase.table('retraining_data').insert({
            'document_id': request.document_id,
            'document_text': document_text,
            'primary_tag_ids': primary_tag_ids if primary_tag_ids else None,
            'secondary_tag_ids': secondary_tag_ids if secondary_tag_ids else None,
            'tertiary_tag_ids': tertiary_tag_ids if tertiary_tag_ids else None
        }).execute()

        if not insert_response.data or len(insert_response.data) == 0:
            raise HTTPException(status_code=500, detail='Failed to insert retraining data')

        result = insert_response.data[0]
        logger.info(f"Successfully inserted retraining row for document {request.document_id}")
        logger.info(f"Tags stored - Primary: {len(primary_tag_ids)}, Secondary: {len(secondary_tag_ids)}, Tertiary: {len(tertiary_tag_ids)}")

        return APIResponse(
            status="success",
            message=f"Updated retraining data with tags",
            data={
                'retraining_id': result['id'],
                'document_id': request.document_id,
                'primary_tag_count': len(primary_tag_ids),
                'secondary_tag_count': len(secondary_tag_ids),
                'tertiary_tag_count': len(tertiary_tag_ids),
                'primary_tag_ids': primary_tag_ids,
                'secondary_tag_ids': secondary_tag_ids,
                'tertiary_tag_ids': tertiary_tag_ids
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update retraining tags: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/retraining/data/{document_id}")
async def get_retraining_data(document_id: int):
    """Get all retraining data rows for a specific document"""
    try:
        # Get retraining data rows for this document
        response = supabase.table('retraining_data').select('*').eq('document_id', document_id).order('id').execute()

        if not response.data or len(response.data) == 0:
            return APIResponse(
                status="success",
                message="No retraining data found for this document",
                data={'rows': []}
            )

        # Get tag names for all tag IDs in the results
        tag_ids = set()
        for row in response.data:
            if row.get('primary_tag_ids'):
                tag_ids.update(row['primary_tag_ids'])
            if row.get('secondary_tag_ids'):
                tag_ids.update(row['secondary_tag_ids'])
            if row.get('tertiary_tag_ids'):
                tag_ids.update(row['tertiary_tag_ids'])

        # Fetch all tag names in one query
        tag_names = {}
        if tag_ids:
            tags_response = supabase.table('tags').select('id, tag_name').in_('id', list(tag_ids)).execute()
            if tags_response.data:
                tag_names = {tag['id']: tag['tag_name'] for tag in tags_response.data}

        # Build response data
        data = []
        for row in response.data:
            text = row.get('document_text', '')

            # Build tag lists with names
            primary_tags = [
                {'id': tag_id, 'name': tag_names.get(tag_id)}
                for tag_id in (row.get('primary_tag_ids') or [])
            ]
            secondary_tags = [
                {'id': tag_id, 'name': tag_names.get(tag_id)}
                for tag_id in (row.get('secondary_tag_ids') or [])
            ]
            tertiary_tags = [
                {'id': tag_id, 'name': tag_names.get(tag_id)}
                for tag_id in (row.get('tertiary_tag_ids') or [])
            ]

            data.append({
                'id': row['id'],
                'document_id': row['document_id'],
                'text_preview': text[:200] + '...' if len(text) > 200 else text,
                'text_length': len(text),
                'primary_tags': primary_tags,
                'secondary_tags': secondary_tags,
                'tertiary_tags': tertiary_tags,
                'created_at': row.get('created_at'),
                'updated_at': row.get('updated_at')
            })

        return APIResponse(
            status="success",
            message=f"Found {len(data)} retraining rows",
            data={'rows': data, 'count': len(data)}
        )

    except Exception as e:
        logger.error(f"Failed to get retraining data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/retraining/stats")
async def get_stats():
    """Get statistics about retraining data"""
    try:
        # Fetch all retraining data (select only needed fields for efficiency)
        response = supabase.table('retraining_data').select('document_id, primary_tag_ids, secondary_tag_ids, tertiary_tag_ids, document_text').execute()

        if not response.data:
            return APIResponse(
                status="success",
                message="Retraining statistics retrieved",
                data={
                    'total_rows': 0,
                    'unique_documents': 0,
                    'rows_with_tags': 0,
                    'avg_text_length': 0
                }
            )

        # Calculate statistics
        total_rows = len(response.data)
        unique_documents = len(set(row['document_id'] for row in response.data))
        rows_with_tags = sum(1 for row in response.data
                            if (row.get('primary_tag_ids') and len(row['primary_tag_ids']) > 0) or
                               (row.get('secondary_tag_ids') and len(row['secondary_tag_ids']) > 0) or
                               (row.get('tertiary_tag_ids') and len(row['tertiary_tag_ids']) > 0))

        # Calculate average text length
        text_lengths = [len(row.get('document_text', '')) for row in response.data]
        avg_text_length = round(sum(text_lengths) / len(text_lengths)) if text_lengths else 0

        return APIResponse(
            status="success",
            message="Retraining statistics retrieved",
            data={
                'total_rows': total_rows,
                'unique_documents': unique_documents,
                'rows_with_tags': rows_with_tags,
                'avg_text_length': avg_text_length
            }
        )

    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/retraining/export-csv")
async def export_csv():
    """
    Export retraining data as CSV with hierarchical tag structure.
    Each row represents a valid hierarchy path (primary -> secondary -> tertiary).
    """
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import io
        from typing import Set, Tuple

        # Fetch all retraining data
        response = supabase.table('retraining_data').select('*').execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail='No retraining data found')

        # Collect all unique tag IDs
        all_tag_ids = set()
        for row in response.data:
            if row.get('primary_tag_ids'):
                all_tag_ids.update(row['primary_tag_ids'])
            if row.get('secondary_tag_ids'):
                all_tag_ids.update(row['secondary_tag_ids'])
            if row.get('tertiary_tag_ids'):
                all_tag_ids.update(row['tertiary_tag_ids'])

        # Fetch ALL tag data (we need parent_id info for tags not in the confirmed lists)
        tag_data = {}
        tags_response = supabase.table('tags').select('id, tag_name, parent_id').execute()
        if tags_response.data:
            tag_data = {tag['id']: {'name': tag['tag_name'], 'parent_id': tag['parent_id']} for tag in tags_response.data}

        # Helper function to find parent in hierarchy
        def find_parent_in_list(tag_id: int, tag_ids_list: list) -> int | None:
            """Find if the parent of tag_id exists in tag_ids_list"""
            if tag_id not in tag_data:
                return None
            parent_id = tag_data[tag_id].get('parent_id')
            if parent_id and parent_id in tag_ids_list:
                return parent_id
            return None

        def find_grandparent_in_list(tag_id: int, tag_ids_list: list) -> int | None:
            """Find if the grandparent of tag_id exists in tag_ids_list"""
            if tag_id not in tag_data:
                return None
            parent_id = tag_data[tag_id].get('parent_id')
            if not parent_id or parent_id not in tag_data:
                return None
            grandparent_id = tag_data[parent_id].get('parent_id')
            if grandparent_id and grandparent_id in tag_ids_list:
                return grandparent_id
            return None

        # Build CSV in memory
        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(['document_id', 'document_text', 'primary_tag', 'secondary_tag', 'tertiary_tag'])

        for row in response.data:
            document_id = row.get('document_id', '')
            document_text = row.get('document_text', '')
            primary_ids = row.get('primary_tag_ids') or []
            secondary_ids = row.get('secondary_tag_ids') or []
            tertiary_ids = row.get('tertiary_tag_ids') or []

            # Track which tags have been used to avoid duplicates
            used_combinations: Set[Tuple[int | None, int | None, int | None]] = set()

            # 1. Start from tertiary tags and trace upward
            for tertiary_id in tertiary_ids:
                secondary_id = find_parent_in_list(tertiary_id, secondary_ids)
                primary_id = None

                if secondary_id:
                    # Found matching secondary, now find primary
                    primary_id = find_parent_in_list(secondary_id, primary_ids)
                else:
                    # Secondary not in list, check if grandparent (primary) is in list
                    primary_id = find_grandparent_in_list(tertiary_id, primary_ids)

                # Build the row
                primary_name = tag_data[primary_id]['name'] if primary_id and primary_id in tag_data else None
                secondary_name = tag_data[secondary_id]['name'] if secondary_id and secondary_id in tag_data else None
                tertiary_name = tag_data[tertiary_id]['name'] if tertiary_id in tag_data else None

                combination = (primary_id, secondary_id, tertiary_id)
                if combination not in used_combinations:
                    csv_writer.writerow([document_id, document_text, primary_name or '', secondary_name or '', tertiary_name or ''])
                    used_combinations.add(combination)

            # 2. Process secondary tags that weren't traced from tertiary
            for secondary_id in secondary_ids:
                # Check if this secondary was already used
                already_used = any(combo[1] == secondary_id for combo in used_combinations)
                if already_used:
                    continue

                # Find its primary parent
                primary_id = find_parent_in_list(secondary_id, primary_ids)

                primary_name = tag_data[primary_id]['name'] if primary_id and primary_id in tag_data else None
                secondary_name = tag_data[secondary_id]['name'] if secondary_id in tag_data else None

                combination = (primary_id, secondary_id, None)
                if combination not in used_combinations:
                    csv_writer.writerow([document_id, document_text, primary_name or '', secondary_name or '', ''])
                    used_combinations.add(combination)

            # 3. Process primary tags that weren't traced at all
            for primary_id in primary_ids:
                # Check if this primary was already used
                already_used = any(combo[0] == primary_id for combo in used_combinations)
                if already_used:
                    continue

                primary_name = tag_data[primary_id]['name'] if primary_id in tag_data else None

                combination = (primary_id, None, None)
                if combination not in used_combinations:
                    csv_writer.writerow([document_id, document_text, primary_name or '', '', ''])
                    used_combinations.add(combination)

        # Prepare the CSV for download
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=retraining_data.csv"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5009,
        reload=True,
        log_level="info"
    )
