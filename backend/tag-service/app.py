# backend/tag-service/app.py
from __future__ import annotations

import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator 
from supabase import Client, create_client             
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Tag Service",
    version="1.0.0",
    description="3-level tag taxonomy (Primary / Secondary / Tertiary) backed by Supabase",
)

# Allow frontend (Next.js) to call the service directly or via proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------- Models -----------------------------

class AddTagIn(BaseModel):
    layer: str = Field(pattern=r"^(primary|secondary|tertiary)$")
    name: str = Field(min_length=1)
    parentPrimary: Optional[str] = None
    parentSecondary: Optional[str] = None

    @field_validator("name")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip()

class RenameTagIn(BaseModel):
    layer: str = Field(pattern=r"^(primary|secondary|tertiary)$")
    oldName: str = Field(min_length=1)
    newName: str = Field(min_length=1)
    parentPrimary: Optional[str] = None
    parentSecondary: Optional[str] = None

    @field_validator("oldName", "newName")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip()

# ----------------------------- Helpers -----------------------------

def fetch_all_tags() -> List[dict]:
    res = sb.table("tags").select("*").order("id").execute()
    return res.data or []

def fetch_tag_by_name(name: str, parent_id: Optional[int]) -> Optional[dict]:
    q = sb.table("tags").select("*").ilike("tag_name", name)
    q = q.is_("parent_id", None) if parent_id is None else q.eq("parent_id", parent_id)
    res = q.execute()
    items = res.data or []
    return items[0] if items else None

def ensure_global_unique(name: str, exclude_id: Optional[int] = None) -> None:
    """
    Enforce global (all layers) case-insensitive uniqueness of tag_name.
    exclude_id: when renaming, ignore the row itself.
    """
    q = sb.table("tags").select("id").ilike("tag_name", name.strip())
    if exclude_id is not None:
        q = q.neq("id", exclude_id)
    res = q.execute()
    if res.data and len(res.data) > 0:
        raise HTTPException(status_code=409, detail="Tag name already exists globally.")

def resolve_scope_ids(
    parent_primary_name: Optional[str],
    parent_secondary_name: Optional[str],
) -> Dict[str, Optional[int]]:
    """
    Return primary_id and secondary_id for current scope.
    """
    primary_id: Optional[int] = None
    secondary_id: Optional[int] = None

    if parent_primary_name:
        p = fetch_tag_by_name(parent_primary_name, None)
        if not p:
            raise HTTPException(status_code=400, detail=f'Primary "{parent_primary_name}" not found')
        primary_id = p["id"]

    if parent_secondary_name:
        if primary_id is None:
            raise HTTPException(status_code=400, detail="Secondary requires a valid Primary parent")
        s = fetch_tag_by_name(parent_secondary_name, primary_id)
        if not s:
            raise HTTPException(
                status_code=400,
                detail=f'Secondary "{parent_secondary_name}" under "{parent_primary_name}" not found',
            )
        secondary_id = s["id"]

    return {"primary_id": primary_id, "secondary_id": secondary_id}

def build_hierarchy(rows: List[dict]) -> Dict[str, Dict[str, List[str]]]:
    """
    Build { Primary: { Secondary: [tertiary...] } } from simple parent_id relationships.
    """
    by_parent: Dict[Optional[int], List[dict]] = {}
    for r in rows:
        by_parent.setdefault(r["parent_id"], []).append(r)

    hierarchy: Dict[str, Dict[str, List[str]]] = {}

    # primaries (parent_id is NULL)
    for primary in by_parent.get(None, []):
        p_name = primary["tag_name"]
        p_id = primary["id"]
        hierarchy[p_name] = {}

        # secondaries
        for secondary in by_parent.get(p_id, []):
            s_name = secondary["tag_name"]
            s_id = secondary["id"]
            tert_rows = by_parent.get(s_id, [])
            hierarchy[p_name][s_name] = [t["tag_name"] for t in tert_rows]

    return hierarchy

# ----------------------------- Routes -----------------------------

@app.get("/tags")
def get_tags() -> Dict[str, Dict[str, List[str]]]:
    """
    Returns the full 3-level hierarchy:
    { "Disclosure": { "SEC_Filings": ["10-K", "S-1"], ... }, ... }
    """
    tags = fetch_all_tags()
    return build_hierarchy(tags)
    

@app.post("/tags", status_code=201)
def add_tag(body: AddTagIn) -> dict:
    """
    Add a new tag.
    - primary: { layer, name }
    - secondary: { layer, name, parentPrimary }
    - tertiary: { layer, name, parentPrimary, parentSecondary }
    """
    scope = resolve_scope_ids(body.parentPrimary, body.parentSecondary)

    if body.layer == "primary":
        parent_id = None
    elif body.layer == "secondary":
        parent_id = scope["primary_id"]
        if parent_id is None:
            raise HTTPException(status_code=400, detail="Secondary requires parentPrimary")
    else:
        parent_id = scope["secondary_id"]
        if parent_id is None:
            raise HTTPException(status_code=400, detail="Tertiary requires parentPrimary and parentSecondary")

    ensure_global_unique(body.name)


    res = sb.table("tags").insert({"tag_name": body.name, "parent_id": parent_id}).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create tag")

    return {"message": "Tag created", "id": res.data[0]["id"]}

@app.patch("/tags/rename")
def rename_tag(body: RenameTagIn) -> dict:
    """
    Rename a tag within its scope.
    """
    scope = resolve_scope_ids(body.parentPrimary, body.parentSecondary)

    if body.layer == "primary":
        parent_id = None
    elif body.layer == "secondary":
        parent_id = scope["primary_id"]
        if parent_id is None:
            raise HTTPException(status_code=400, detail="Secondary requires parentPrimary")
    else:
        parent_id = scope["secondary_id"]
        if parent_id is None:
            raise HTTPException(status_code=400, detail="Tertiary requires parentPrimary and parentSecondary")

    target = fetch_tag_by_name(body.oldName, parent_id)
    if not target:
        raise HTTPException(status_code=404, detail="Tag to rename not found in this scope")

    if body.oldName.strip().lower() != body.newName.strip().lower():
        ensure_global_unique(body.newName, exclude_id=target["id"])


    res = sb.table("tags").update({"tag_name": body.newName}).eq("id", target["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to update tag")

    return {"message": "Tag updated"}

@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int) -> dict:
    """
    Optional: delete a tag (children removed by FK cascade if configured).
    """
    res = sb.table("tags").delete().eq("id", tag_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted"}


@app.get("/tags/e2e")
def e2e_test():
    """
    Simple endpoint to test connectivity to Supabase and service health.
    Returns count of tags or error message if connection fails.
    """
    try:
        res = sb.table("tags").select("id").limit(1).execute()
        if res.data is None:
            return {"status": "fail", "message": "No data returned from Supabase"}
        return {"status": "success", "message": "Connected to Supabase", "tag_sample_count": len(res.data)}
    except Exception as e:
        return {"status": "error", "message": f"Supabase connection failed: {str(e)}"}
