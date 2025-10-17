from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class TagCreate(BaseModel):
    tag_name: str
    parent_id: int | None = None

class TagDelete(BaseModel):
    id: int

def build_tag_hierarchy(tags):
    tags_by_id = {tag['id']: tag for tag in tags}
    children_map = {}
    for tag in tags:
        pid = tag['parent_id']
        if pid is not None:
            children_map.setdefault(pid, []).append(tag)

    def build_node(tag):
        tname = tag['tag_name']
        tid = tag['id']
        children = children_map.get(tid, [])
        if not children:
            return []
        # If children are all leaves, return list of their tag_names
        if all(len(children_map.get(child['id'], [])) == 0 for child in children):
            return [child['tag_name'] for child in children]
        # Otherwise, recurse and build nested dict/list
        result = {}
        for child in children:
            node = build_node(child)
            result[child['tag_name']] = node
        return result

    # Build only for parents (those with parent_id is None)
    top_tags = [tag for tag in tags if tag['parent_id'] is None]
    hierarchy = {}
    for top in top_tags:
        node = build_node(top)
        hierarchy[top['tag_name']] = node
    return hierarchy

@app.get("/tags")
async def get_tags():
    response = supabase.table('tags').select('*').execute()
    tags = response.data
    tag_structure = build_tag_hierarchy(tags)
    return tag_structure

@app.post("/tags")
async def create_tag(tag: TagCreate):
    """Add a new tag"""
    data = {"tag_name": tag.tag_name, "parent_id": tag.parent_id}
    response = supabase.table("tags").insert(data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Tag creation failed")

    return {"message": "Tag added successfully", "created_tag": response.data[0]}


@app.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int):
    """Delete a tag and its children (if any)"""
    response = supabase.table("tags").delete().eq("id", tag_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail=f"Tag with id {tag_id} not found")

    return {"message": f"Tag {tag_id} deleted successfully"}

