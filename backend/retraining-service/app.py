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

class HierarchyInfo(BaseModel):
    retraining_id: int
    hierarchy: str
    primary_tag_id: int
    secondary_tag_id: int
    tertiary_tag_id: int

class TagHierarchyDetail(BaseModel):
    id: Optional[int]
    name: Optional[str]

class RetrainingDataRow(BaseModel):
    id: int
    document_id: int
    text_preview: str
    text_length: int
    hierarchy: Dict[str, TagHierarchyDetail]
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

    This will create multiple rows if there are multiple valid tag hierarchies.
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
            # If no existing data, we'll need the text from somewhere else
            # For now, we'll raise an error but with a more helpful message
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

        # Look up all tag IDs at once
        all_tag_names = [t.tag for t in tags_list]
        tag_lookup = {}

        if all_tag_names:
            tags_response = supabase.table('tags').select('id, tag_name').in_('tag_name', all_tag_names).execute()
            if tags_response.data:
                tag_lookup = {tag['tag_name']: tag['id'] for tag in tags_response.data}

        # Build hierarchies from confirmed tags
        # Simply use the tags as they are confirmed by the user
        valid_hierarchies = []

        # Get primary, secondary, tertiary tag IDs
        primary_tag_ids = {}
        secondary_tag_ids = {}
        tertiary_tag_ids = {}

        for tag in primary_tags:
            tag_id = tag_lookup.get(tag.tag)
            if tag_id:
                primary_tag_ids[tag.tag] = tag_id
            else:
                logger.warning(f"Primary tag '{tag.tag}' not found in tags table")

        for tag in secondary_tags:
            tag_id = tag_lookup.get(tag.tag)
            if tag_id:
                secondary_tag_ids[tag.tag] = tag_id
            else:
                logger.warning(f"Secondary tag '{tag.tag}' not found in tags table")

        for tag in tertiary_tags:
            tag_id = tag_lookup.get(tag.tag)
            if tag_id:
                tertiary_tag_ids[tag.tag] = tag_id
            else:
                logger.warning(f"Tertiary tag '{tag.tag}' not found in tags table")

        # Create hierarchy entries for each combination
        # If user confirmed these tags together, we store them together
        if primary_tag_ids or secondary_tag_ids or tertiary_tag_ids:
            # Get the first (or only) tag from each level
            primary_name = list(primary_tag_ids.keys())[0] if primary_tag_ids else None
            secondary_name = list(secondary_tag_ids.keys())[0] if secondary_tag_ids else None
            tertiary_name = list(tertiary_tag_ids.keys())[0] if tertiary_tag_ids else None

            primary_id = primary_tag_ids.get(primary_name) if primary_name else None
            secondary_id = secondary_tag_ids.get(secondary_name) if secondary_name else None
            tertiary_id = tertiary_tag_ids.get(tertiary_name) if tertiary_name else None

            if primary_id or secondary_id or tertiary_id:
                hierarchy_display = " → ".join(filter(None, [primary_name, secondary_name, tertiary_name]))
                valid_hierarchies.append({
                    'primary_id': primary_id,
                    'secondary_id': secondary_id,
                    'tertiary_id': tertiary_id,
                    'primary_name': primary_name,
                    'secondary_name': secondary_name,
                    'tertiary_name': tertiary_name
                })
                logger.info(f"Valid hierarchy: {hierarchy_display}")

        if not valid_hierarchies:
            logger.warning(f"No tags found in database for document {request.document_id}")
            raise HTTPException(
                status_code=400,
                detail='No valid tags found in database - Make sure confirmed tags exist in the tags table'
            )

        # Delete old rows for this document ONLY AFTER we successfully built new hierarchies
        # This ensures we don't lose data if hierarchy building fails
        supabase.table('retraining_data').delete().eq('document_id', request.document_id).execute()
        logger.info(f"Deleted old retraining rows for document {request.document_id}")

        # Insert rows for each valid hierarchy
        inserted_rows = []
        for hierarchy in valid_hierarchies:
            insert_response = supabase.table('retraining_data').insert({
                'document_id': request.document_id,
                'document_text': document_text,
                'primary_tag_id': hierarchy['primary_id'],
                'secondary_tag_id': hierarchy['secondary_id'],
                'tertiary_tag_id': hierarchy['tertiary_id']
            }).execute()

            if insert_response.data and len(insert_response.data) > 0:
                result = insert_response.data[0]
                inserted_rows.append({
                    'retraining_id': result['id'],
                    'hierarchy': f"{hierarchy['primary_name']} → {hierarchy['secondary_name']} → {hierarchy['tertiary_name']}",
                    'primary_tag_id': result['primary_tag_id'],
                    'secondary_tag_id': result['secondary_tag_id'],
                    'tertiary_tag_id': result['tertiary_tag_id']
                })

        logger.info(f"Successfully inserted {len(inserted_rows)} retraining rows for document {request.document_id}")

        return APIResponse(
            status="success",
            message=f"Updated retraining data with {len(inserted_rows)} tag hierarchies",
            data={
                'document_id': request.document_id,
                'hierarchies_count': len(inserted_rows),
                'hierarchies': inserted_rows
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
            if row.get('primary_tag_id'):
                tag_ids.add(row['primary_tag_id'])
            if row.get('secondary_tag_id'):
                tag_ids.add(row['secondary_tag_id'])
            if row.get('tertiary_tag_id'):
                tag_ids.add(row['tertiary_tag_id'])

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
            data.append({
                'id': row['id'],
                'document_id': row['document_id'],
                'text_preview': text[:200] + '...' if len(text) > 200 else text,
                'text_length': len(text),
                'hierarchy': {
                    'primary': {
                        'id': row.get('primary_tag_id'),
                        'name': tag_names.get(row.get('primary_tag_id'))
                    },
                    'secondary': {
                        'id': row.get('secondary_tag_id'),
                        'name': tag_names.get(row.get('secondary_tag_id'))
                    },
                    'tertiary': {
                        'id': row.get('tertiary_tag_id'),
                        'name': tag_names.get(row.get('tertiary_tag_id'))
                    }
                },
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
        response = supabase.table('retraining_data').select('document_id, primary_tag_id, document_text').execute()

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
        rows_with_tags = sum(1 for row in response.data if row.get('primary_tag_id') is not None)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5009,
        reload=True,
        log_level="info"
    )
