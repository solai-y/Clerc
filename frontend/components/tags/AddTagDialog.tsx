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
  onSubmit: (payload: { tag_name: string; parent_id: number | null; parent_path?: string[] }) => Promise<void>;
  allTags: TagNode[];                 // NOTE: these nodes include .tier (set in page.tsx)
  preselectParent?: TagNode | null;
};

export default function AddTagDialog({
  open,
  onOpenChange,
  onSubmit,
  allTags,
  preselectParent = null,
}: Props) {
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // flatten the tree WITH labels; EXCLUDE tertiary nodes (you can only add under primary/secondary)
  const flatParents = useMemo(() => {
    const out: { id: number; label: string; tier?: TagNode["tier"] }[] = [];
    const walk = (n: TagNode, path: string[] = []) => {
      const label = [...path, n.tag_name].join(" / ");
      // only include non-tertiary nodes as selectable parents
      if (n.tier !== "tertiary") out.push({ id: n.id, label, tier: n.tier });
      n.children?.forEach((c) => walk(c, [...path, n.tag_name]));
    };
    allTags.forEach((n) => walk(n));
    return out;
  }, [allTags]);

  // Find helper by id inside flattened set
  const findFlatById = (id: number | null) =>
    id == null ? undefined : flatParents.find((o) => o.id === id);

  useEffect(() => {
    setError(null);
    setName("");
    // If a tertiary node was passed in, ignore it (force None / Primary)
    if (preselectParent && preselectParent.tier !== "tertiary") {
      setParentId(preselectParent.id);
    } else {
      setParentId(null);
    }
  }, [open, preselectParent]);

  const selectValue = parentId === null ? undefined : String(parentId);

  async function handleCreate() {
    if (!name.trim()) {
      setError("Tag name is required.");
      return;
    }

    // final guard — parent must be primary/secondary only
    const chosen = findFlatById(parentId);
    if (parentId !== null && !chosen) {
      setError("You can only add under Primary or Secondary.");
      return;
    }

    // Build a name path for the backend (Disclosure / SEC Filings -> ["Disclosure","SEC Filings"])
    let parentPath: string[] | undefined;
    if (chosen) parentPath = chosen.label.split(" / ").map((s) => s.trim()).filter(Boolean);

    setSaving(true);
    setError(null);
    try {
      await onSubmit({
        tag_name: name.trim(),
        parent_id: parentId,
        parent_path: parentPath,
      });
      onOpenChange(false);
    } catch (e: any) {
      setError(e?.message ?? "Failed to create tag.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Tag</DialogTitle>
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
                {flatParents.map((o) => (
                  <SelectItem key={o.id} value={String(o.id)}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              You can only add under <span className="font-medium">Primary</span> or{" "}
              <span className="font-medium">Secondary</span> tags. Tertiary tags can’t have children.
            </p>
          </div>

          {!!error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={saving}>
            {saving ? "Creating..." : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
