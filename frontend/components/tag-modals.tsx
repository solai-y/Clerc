"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTags } from "@/contexts/tag-context";

type AddInit = {
  level: "primary" | "secondary" | "tertiary";
  parent?: { primary?: string; secondary?: string };
};
type EditInit = {
  level: "primary" | "secondary" | "tertiary";
  currentName: string;
  parent?: { primary?: string; secondary?: string };
};

export const AddTagModal: React.FC<{
  open: boolean;
  initial: AddInit;
  onOpenChange: (v: null) => void;
}> = ({ open, onOpenChange, initial }) => {
  const { tree, addTag, isUnique } = useTags();

  // Keep local state in sync with props EACH TIME the modal opens
  const [level, setLevel] = useState<"primary" | "secondary" | "tertiary">(initial.level);
  const [primary, setPrimary] = useState<string>(initial.parent?.primary ?? "");
  const [secondary, setSecondary] = useState<string>(initial.parent?.secondary ?? "");
  const [name, setName] = useState("");

  useEffect(() => {
    if (open) {
      setLevel(initial.level);
      setPrimary(initial.parent?.primary ?? "");
      setSecondary(initial.parent?.secondary ?? "");
      setName("");
    }
  }, [open, initial.level, initial.parent?.primary, initial.parent?.secondary]);

  const primaryOptions = useMemo(() => Object.keys(tree).sort(), [tree]);
  const secondaryOptions = useMemo(
    () => (primary ? Object.keys(tree[primary] ?? {}).sort() : []),
    [primary, tree]
  );

  const valid =
    level === "primary"
      ? !!name.trim()
      : level === "secondary"
      ? !!name.trim() && !!primary
      : !!name.trim() && !!primary && !!secondary;

  const uniqueOk =
    !valid
      ? false
      : isUnique(
          level,
          name,
          level === "primary"
            ? undefined
            : level === "secondary"
            ? { primary }
            : { primary, secondary }
        );

  const [err, setErr] = useState<string | null>(null);

  const onSubmit = async () => {
    setErr(null);
    try {
      await addTag({
        layer: level,
        name: name.trim(),
        parentPrimary: level === "primary" ? undefined : primary,
        parentSecondary: level === "tertiary" ? secondary : undefined,
      });
      onOpenChange(null);
    } catch (e: any) {
      setErr(e?.message || "Failed to add tag.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={() => onOpenChange(null)}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Tag</DialogTitle>
          <DialogDescription>
            Create a new tag at the chosen hierarchy level.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-2">
            <Label>Level</Label>
            <Select value={level} onValueChange={(v: any) => setLevel(v)}>
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

          {level !== "primary" && (
            <div className="grid gap-2">
              <Label>Parent Primary</Label>
              <Select value={primary} onValueChange={setPrimary}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose primary…" />
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
            <div className="grid gap-2">
              <Label>Parent Secondary</Label>
              <Select value={secondary} onValueChange={setSecondary} disabled={!primary}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose secondary…" />
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

          <div className="grid gap-2">
            <Label>Tag Name</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Product_Launch"
            />
          </div>

          {valid && !uniqueOk && (
            <p className="text-xs text-red-600">Tag name already exists in this scope.</p>
          )}
          {err && <p className="text-xs text-red-600">{err}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(null)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={!valid || !uniqueOk}>
            Add
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export const EditTagModal: React.FC<{
  open: boolean;
  initial: EditInit;
  onOpenChange: (v: null) => void;
}> = ({ open, onOpenChange, initial }) => {
  const { updateTag, isUnique } = useTags();
  const [newName, setNewName] = useState(initial.currentName);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setNewName(initial.currentName);
      setErr(null);
    }
  }, [open, initial.currentName]);

  const sameName =
    newName.trim().toLowerCase() === initial.currentName.trim().toLowerCase();

  const uniqueOk =
    sameName ||
    isUnique(initial.level, newName, {
      primary: initial.parent?.primary,
      secondary: initial.parent?.secondary,
    });

  const save = async () => {
    setErr(null);
    try {
      await updateTag({
        layer: initial.level,
        oldName: initial.currentName,
        newName: newName.trim(),
        parentPrimary: initial.parent?.primary,
        parentSecondary: initial.parent?.secondary,
      });
      onOpenChange(null);
    } catch (e: any) {
      setErr(e?.message || "Failed to update tag.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={() => onOpenChange(null)}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Tag</DialogTitle>
          <DialogDescription>
            Rename the selected tag. Uniqueness is validated within its scope.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-2">
            <Label>Current Name</Label>
            <Input value={initial.currentName} readOnly />
          </div>
          <div className="grid gap-2">
            <Label>New Name</Label>
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
          </div>
          {!sameName && !uniqueOk && (
            <p className="text-xs text-red-600">
              New name would duplicate an existing tag in this scope.
            </p>
          )}
          {err && <p className="text-xs text-red-600">{err}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(null)}>
            Cancel
          </Button>
          <Button onClick={save} disabled={!newName.trim() || !uniqueOk}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
