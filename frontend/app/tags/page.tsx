"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Plus } from "lucide-react";

import { TagTree } from "@/components/tags/TagTree";
import AddTagDialog from "@/components/tags/AddTagDialog";
import DeleteTagDialog from "@/components/tags/DeleteTagDialog";
import EditTagDialog from "@/components/tags/EditTagDialog";
import { createTag, deleteTag, getTags, updateTag, type TagNode } from "@/lib/tag-api";

// annotate tiers by depth (0 = primary, 1 = secondary, 2+ = tertiary)
function withTiers(nodes: TagNode[], depth = 0): TagNode[] {
  return nodes.map((n) => {
    const tier: TagNode["tier"] = depth === 0 ? "primary" : depth === 1 ? "secondary" : "tertiary";
    return {
      ...n,
      tier,
      children: n.children ? withTiers(n.children, depth + 1) : [],
    };
  });
}

export default function TagHierarchyPage() {
  const [data, setData] = useState<TagNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);

  const [selectedParent, setSelectedParent] = useState<TagNode | null>(null);
  const [selectedDelete, setSelectedDelete] = useState<TagNode | null>(null);
  const [selectedEdit, setSelectedEdit] = useState<TagNode | null>(null);

  const [filter, setFilter] = useState("");

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const raw = await getTags();
      setData(withTiers(raw));
    } catch (e: any) {
      setError(e?.message ?? "Failed to load tag hierarchy.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const filtered = useMemo(() => {
    if (!filter.trim()) return data;
    const q = filter.toLowerCase();
    const filterTree = (node: TagNode): TagNode | null => {
      const matched = node.tag_name.toLowerCase().includes(q);
      const kids = (node.children || []).map(filterTree).filter(Boolean) as TagNode[];
      if (matched || kids.length) return { ...node, children: kids };
      return null;
    };
    return data.map(filterTree).filter(Boolean) as TagNode[];
  }, [data, filter]);

  function openAdd(parent?: TagNode) {
    setSelectedParent(parent ?? null);
    setCreateOpen(true);
  }
  function openDelete(tag: TagNode) {
    setSelectedDelete(tag);
    setDeleteOpen(true);
  }
  function openEdit(tag: TagNode) {
    setSelectedEdit(tag);
    setEditOpen(true);
  }

  async function handleCreate(payload: { tag_name: string; parent_id: number | null }) {
    await createTag(payload);
    await refresh();
  }
  async function handleDeleteConfirmed(tag: TagNode) {
    await deleteTag(tag.id);
    await refresh();
  }
  async function handleEditConfirmed(payload: { id: number; tag_name: string; parent_id: number | null }) {
    await updateTag(payload);
    await refresh();
  }

  return (
    <div className="container mx-auto max-w-6xl py-6">
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Tag Hierarchy</CardTitle>
            <p className="text-sm text-muted-foreground">
              View the complete tag taxonomy (Primary → Secondary → Tertiary). You can add, edit, and delete tags here.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Input
              className="w-64"
              placeholder="Search tag names..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
            <Button onClick={() => openAdd()}>
              <Plus className="h-4 w-4 mr-2" />
              Add Tag
            </Button>
          </div>
        </CardHeader>
        <Separator />
        <CardContent className="pt-4">
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading taxonomy…</div>
          ) : error ? (
            <div className="text-sm text-red-600">{error}</div>
          ) : (
            <TagTree data={filtered} onAdd={openAdd} onDelete={openDelete} onEdit={openEdit} />
          )}
        </CardContent>
      </Card>

      {/* dialogs */}
      <AddTagDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSubmit={handleCreate}
        allTags={data}
        preselectParent={selectedParent}
      />
      <DeleteTagDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        tag={selectedDelete}
        onConfirm={handleDeleteConfirmed}
      />
      <EditTagDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        tag={selectedEdit}
        allTags={data}
        onSubmit={handleEditConfirmed}
      />
    </div>
  );
}
