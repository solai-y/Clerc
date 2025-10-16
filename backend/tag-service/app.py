from fastapi import FastAPI
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

