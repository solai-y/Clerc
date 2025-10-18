"use client";
import { useEffect, useMemo, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import type { TagNode } from "@/lib/tag-api";

const NONE = "__NONE__";

type Props = {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  tag: TagNode | null;
  allTags: TagNode[];
  onSubmit: (payload: { id: number; tag_name: string; parent_id: number | null }) => Promise<void>;
};

export default function EditTagDialog({ open, onOpenChange, tag, allTags, onSubmit }: Props) {
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Flatten tree for parent options
  const flat = useMemo(() => {
    const out: { id: number; label: string; node: TagNode }[] = [];
    const walk = (n: TagNode, path: string[] = []) => {
      const label = [...path, n.tag_name].join(" / ");
      out.push({ id: n.id, label, node: n });
      n.children?.forEach((c) => walk(c, [...path, n.tag_name]));
    };
    allTags.forEach((n) => walk(n));
    return out;
  }, [allTags]);

  // Prevent choosing self/descendants
  const forbidden = useMemo(() => {
    const ids = new Set<number>();
    if (!tag) return ids;
    const collect = (n: TagNode) => {
      ids.add(n.id);
      n.children?.forEach(collect);
    };
    collect(tag);
    return ids;
  }, [tag]);

  useEffect(() => {
    setError(null);
    if (tag) {
      setName(tag.tag_name);
      setParentId(tag.parent_id ?? null);
    } else {
      setName("");
      setParentId(null);
    }
  }, [open, tag]);

  const selectValue = parentId === null ? undefined : String(parentId); // undefined shows placeholder

  async function handleSave() {
    if (!tag) return;
    if (!name.trim()) {
      setError("Tag name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        id: tag.id,
        tag_name: name.trim(),
        parent_id: parentId,
      });
      onOpenChange(false);
    } catch (e: any) {
      setError(e?.message ?? "Failed to update tag.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Tag</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-1.5">
            <Label htmlFor="tag-name">Name</Label>
            <Input id="tag-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div className="grid gap-1.5">
            <Label>Parent</Label>
            <Select
              value={selectValue}
              onValueChange={(v) => setParentId(v === NONE ? null : Number(v))}
            >
              <SelectTrigger>
                <SelectValue placeholder="None (Primary)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE}>None (Primary)</SelectItem>
                {flat
                  .filter((o) => !forbidden.has(o.id))
                  .map((o) => (
                    <SelectItem key={o.id} value={String(o.id)}>
                      {o.label}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              You can re-parent this tag. You cannot select the tag itself or its own descendants.
            </p>
          </div>

          {!!error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
