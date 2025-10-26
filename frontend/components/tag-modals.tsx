"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { useTags } from "@/contexts/tag-context";
import { useToast } from "@/hooks/use-toast";

/* -------------------- Types used by both modals -------------------- */
export type AddInit = {
  level: "primary" | "secondary" | "tertiary";
  parent?: { primary?: string; secondary?: string };
};

export type EditInit = {
  level: "primary" | "secondary" | "tertiary";
  currentName: string;
  parent?: { primary?: string; secondary?: string };
};

type Status = { kind: "idle" } | { kind: "error"; message: string };

/* =======================================================================
   AddTagModal
   ======================================================================= */
interface AddTagModalProps {
  open: boolean;
  initial: AddInit;
  onOpenChange: (next: null | AddInit) => void;
}

export const AddTagModal: React.FC<AddTagModalProps> = ({ open, initial, onOpenChange }) => {
  const { tree, addTag } = useTags();
  const { toast } = useToast();

  const [level, setLevel] = useState<"primary" | "secondary" | "tertiary">(initial.level);
  const [name, setName] = useState<string>("");

  const [parentPrimary, setParentPrimary] = useState<string | undefined>(initial.parent?.primary);
  const [parentSecondary, setParentSecondary] = useState<string | undefined>(initial.parent?.secondary);

  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  useEffect(() => {
    if (!open) return;
    setLevel(initial.level);
    setName("");
    setParentPrimary(initial.parent?.primary);
    setParentSecondary(initial.parent?.secondary);
    setSubmitting(false);
    setStatus({ kind: "idle" });
  }, [open, initial]);

  const primaryOptions = useMemo(() => Object.keys(tree).sort(), [tree]);
  const secondaryOptions = useMemo(() => {
    if (!parentPrimary) return [];
    return Object.keys(tree[parentPrimary] || {}).sort();
  }, [tree, parentPrimary]);

  useEffect(() => {
    if (level === "primary") {
      setParentPrimary(undefined);
      setParentSecondary(undefined);
    } else if (level === "secondary") {
      if (!parentPrimary && primaryOptions.length > 0) setParentPrimary(primaryOptions[0]);
      setParentSecondary(undefined);
    } else if (level === "tertiary") {
      const p = parentPrimary || primaryOptions[0];
      setParentPrimary(p);
      const secs = Object.keys(tree[p] || {});
      setParentSecondary(parentSecondary && (tree[p] || {})[parentSecondary] ? parentSecondary : secs[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [level]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus({ kind: "idle" });

    if (!name.trim()) {
      setStatus({ kind: "error", message: "Please enter a tag name." });
      return;
    }
    if (level === "secondary" && !parentPrimary) {
      setStatus({ kind: "error", message: "Please select a Primary parent for this Secondary tag." });
      return;
    }
    if (level === "tertiary" && (!parentPrimary || !parentSecondary)) {
      setStatus({ kind: "error", message: "Please select both Primary and Secondary parents." });
      return;
    }

    try {
      setSubmitting(true);
      await addTag({
        layer: level,
        name: name.trim(),
        parentPrimary,
        parentSecondary,
      });

      onOpenChange(null);
      toast({
        title: "Tag added",
        description:
          level === "primary"
            ? `Primary "${name.trim()}" created successfully.`
            : level === "secondary"
            ? `Secondary "${name.trim()}" added under "${parentPrimary}".`
            : `Tertiary "${name.trim()}" added under "${parentPrimary} → ${parentSecondary}".`,
        duration: 5000,
      });
    } catch (err) {
      setStatus({
        kind: "error",
        message: err instanceof Error ? err.message : "Failed to add tag. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={() => onOpenChange(null)}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Tag</DialogTitle>
        </DialogHeader>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {/* Level */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Level</label>
            <Select value={level} onValueChange={(v: "primary" | "secondary" | "tertiary") => setLevel(v)}>
              <SelectTrigger>
                <SelectValue placeholder="Select level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="primary">Primary</SelectItem>
                <SelectItem value="secondary">Secondary</SelectItem>
                <SelectItem value="tertiary">Tertiary</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Parents */}
          {level !== "primary" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Parent Primary</label>
              <Select
                value={parentPrimary ?? ""}
                onValueChange={(v) => {
                  setParentPrimary(v);
                  setParentSecondary(undefined);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select primary" />
                </SelectTrigger>
                <SelectContent>
                  {primaryOptions.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {level === "tertiary" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Parent Secondary</label>
              <Select
                value={parentSecondary ?? ""}
                onValueChange={(v) => setParentSecondary(v)}
                disabled={!parentPrimary}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select secondary" />
                </SelectTrigger>
                <SelectContent>
                  {secondaryOptions.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Tag Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Enter tag name" />
          </div>

          {/* Inline error */}
          {status.kind === "error" && (
            <Alert className="border-red-200 bg-red-50 text-red-800">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription>{status.message}</AlertDescription>
            </Alert>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Adding..." : "Add"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

/* =======================================================================
   EditTagModal (Rename)
   ======================================================================= */
interface EditTagModalProps {
  open: boolean;
  initial: EditInit;
  onOpenChange: (next: null | EditInit) => void;
}

export const EditTagModal: React.FC<EditTagModalProps> = ({ open, initial, onOpenChange }) => {
  const { tree, updateTag } = useTags();
  const { toast } = useToast();

  const [level, setLevel] = useState<"primary" | "secondary" | "tertiary">(initial.level);
  const [oldName, setOldName] = useState<string>(initial.currentName);
  const [newName, setNewName] = useState<string>(initial.currentName);

  const [parentPrimary, setParentPrimary] = useState<string | undefined>(initial.parent?.primary);
  const [parentSecondary, setParentSecondary] = useState<string | undefined>(initial.parent?.secondary);

  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  useEffect(() => {
    if (!open) return;
    setLevel(initial.level);
    setOldName(initial.currentName);
    setNewName(initial.currentName);
    setParentPrimary(initial.parent?.primary);
    setParentSecondary(initial.parent?.secondary);
    setSubmitting(false);
    setStatus({ kind: "idle" });
  }, [open, initial]);

  const primaryOptions = useMemo(() => Object.keys(tree).sort(), [tree]);
  const secondaryOptions = useMemo(() => {
    if (!parentPrimary) return [];
    return Object.keys(tree[parentPrimary] || {}).sort();
  }, [tree, parentPrimary]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus({ kind: "idle" });

    if (!newName.trim()) {
      setStatus({ kind: "error", message: "Please enter a tag name." });
      return;
    }

    try {
      setSubmitting(true);
      await updateTag({
        layer: level,
        oldName,
        newName: newName.trim(),
        parentPrimary,
        parentSecondary,
      });

      onOpenChange(null);
      toast({
        title: "Tag updated",
        description:
          level === "primary"
            ? `Primary renamed to "${newName.trim()}".`
            : level === "secondary"
            ? `Secondary in "${parentPrimary}" renamed to "${newName.trim()}".`
            : `Tertiary in "${parentPrimary} → ${parentSecondary}" renamed to "${newName.trim()}".`,
        duration: 5000,
      });
    } catch (err) {
      setStatus({
        kind: "error",
        message: err instanceof Error ? err.message : "Failed to update tag. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={() => onOpenChange(null)}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Tag</DialogTitle>
        </DialogHeader>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {/* Level (read-only) */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Level</label>
            <Select value={level} onValueChange={() => {}} disabled>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="primary">Primary</SelectItem>
                <SelectItem value="secondary">Secondary</SelectItem>
                <SelectItem value="tertiary">Tertiary</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Parents (read-only) */}
          {level !== "primary" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Parent Primary</label>
              <Select value={parentPrimary ?? ""} onValueChange={() => {}} disabled>
                <SelectTrigger>
                  <SelectValue placeholder="Primary" />
                </SelectTrigger>
                <SelectContent>
                  {primaryOptions.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {level === "tertiary" && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Parent Secondary</label>
              <Select value={parentSecondary ?? ""} onValueChange={() => {}} disabled>
                <SelectTrigger>
                  <SelectValue placeholder="Secondary" />
                </SelectTrigger>
                <SelectContent>
                  {secondaryOptions.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Current name (view-only) */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Current Name</label>
            <div
              className="
                rounded-md border bg-gray-50 text-gray-700
                px-3 py-2 select-none
                cursor-default
              "
              aria-readonly="true"
            >
              {oldName}
            </div>
          </div>

          {/* New name (editable) */}
          <div className="space-y-2">
            <label className="text-sm font-medium">New Name</label>
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter new tag name"
            />
          </div>

          {/* Inline error */}
          {status.kind === "error" && (
            <Alert className="border-red-200 bg-red-50 text-red-800">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription>{status.message}</AlertDescription>
            </Alert>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : "Save"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
