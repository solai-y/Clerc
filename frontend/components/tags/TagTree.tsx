"use client";
import { useState } from "react";
import { ChevronDown, ChevronRight, Plus, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { TagNode } from "@/lib/tag-api";

type Props = {
  data: TagNode[];
  onAdd: (parent?: TagNode) => void;
  onDelete: (tag: TagNode) => void;
  onEdit: (tag: TagNode) => void;
};

function TierBadge({ tier }: { tier?: string }) {
  if (!tier) return null;
  const cls =
    tier === "primary"
      ? "bg-emerald-100 text-emerald-800"
      : tier === "secondary"
      ? "bg-amber-100 text-amber-800"
      : "bg-sky-100 text-sky-800";
  return <Badge className={cn("capitalize", cls)}>{tier}</Badge>;
}

function NodeRow({
  node,
  level,
  onAdd,
  onDelete,
  onEdit,
}: {
  node: TagNode;
  level: number;
  onAdd: (parent: TagNode) => void;
  onDelete: (tag: TagNode) => void;
  onEdit: (tag: TagNode) => void;
}) {
  const [open, setOpen] = useState(true);
  const hasChildren = (node.children?.length ?? 0) > 0;

  // NEW: No add beyond tertiary (level 0=primary,1=secondary,2=tertiary)
  const canAdd = level < 2;

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 py-1 pr-2 rounded-md hover:bg-muted/60",
          level > 0 && "ml-4"
        )}
      >
        {hasChildren ? (
          <button className="p-1" aria-label={open ? "Collapse" : "Expand"} onClick={() => setOpen((v) => !v)}>
            {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <span className="w-4" />
        )}

        <span className="font-medium">{node.tag_name}</span>
        <TierBadge tier={node.tier} />

        <div className="ml-auto flex items-center gap-1">
          {canAdd && (
            <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => onAdd(node)} title="Add child">
              <Plus className="h-4 w-4" />
            </Button>
          )}
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => onEdit(node)} title="Edit">
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 text-red-600 hover:text-red-700"
            onClick={() => onDelete(node)}
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {hasChildren && open && (
        <div className="ml-6">
          {node.children!.map((child) => (
            <NodeRow key={child.id} node={child} level={level + 1} onAdd={onAdd} onDelete={onDelete} onEdit={onEdit} />
          ))}
        </div>
      )}
    </div>
  );
}

export function TagTree({ data, onAdd, onDelete, onEdit }: Props) {
  return (
    <ScrollArea className="h-[calc(100vh-14rem)]">
      <div className="space-y-1">
        {data.map((n) => (
          <NodeRow key={n.id} node={n} level={0} onAdd={onAdd} onDelete={onDelete} onEdit={onEdit} />
        ))}
        {data.length === 0 && (
          <div className="text-sm text-muted-foreground">No tags yet. Create your first tag.</div>
        )}
      </div>
    </ScrollArea>
  );
}
