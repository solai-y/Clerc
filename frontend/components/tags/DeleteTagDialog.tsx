"use client";
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { TagNode } from "@/lib/tag-api";

type Props = {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  tag?: TagNode | null;
  onConfirm: (tag: TagNode) => Promise<void>;
};

export default function DeleteTagDialog({ open, onOpenChange, tag, onConfirm }: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleDelete() {
    if (!tag) return;
    setBusy(true);
    setErr(null);
    try {
      await onConfirm(tag);
      onOpenChange(false);
    } catch (e: any) {
      setErr(e?.message ?? "Delete failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Tag</DialogTitle>
        </DialogHeader>

        <div className="space-y-2">
          <p>
            You’re about to delete <b>{tag?.tag_name}</b>.
          </p>
          <p className="text-sm text-muted-foreground">
            If this tag has child tags, the backend cascade/reassign policy applies. If the tag is currently
            assigned to documents, the backend should reject deletion and explain why.
          </p>
          {!!err && <p className="text-sm text-red-600">{err}</p>}
        </div>

        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)} disabled={busy}>Cancel</Button>
          <Button variant="destructive" onClick={handleDelete} disabled={busy}>
            {busy ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
