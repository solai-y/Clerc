"use client";

import React, { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Edit3, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTags } from "@/contexts/tag-context";
// ✅ use relative path because this file is in the same folder as tag-modals.tsx
import { AddTagModal, EditTagModal } from "./tag-modals";

export const TagTree: React.FC = () => {
  const { tree, loading, error } = useTags();
  const [expandedPrimary, setExpandedPrimary] = useState<Record<string, boolean>>({});
  const [expandedSecondary, setExpandedSecondary] = useState<Record<string, boolean>>({});

  const [addOpen, setAddOpen] = useState<
    | null
    | {
        level: "primary" | "secondary" | "tertiary";
        parent?: { primary?: string; secondary?: string };
      }
  >(null);
  const [editOpen, setEditOpen] = useState<
    | null
    | {
        level: "primary" | "secondary" | "tertiary";
        currentName: string;
        parent?: { primary?: string; secondary?: string };
      }
  >(null);

  const sorted = useMemo(() => {
    const clone: typeof tree = {};
    Object.keys(tree)
      .sort()
      .forEach((p) => {
        const sec = tree[p] || {}; // guard
        clone[p] = {};
        Object.keys(sec)
          .sort()
          .forEach((s) => {
            const tert = sec[s] || []; // guard
            clone[p][s] = [...tert].sort();
          });
      });
    return clone;
  }, [tree]);

  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-gray-500">
          Loading tag hierarchy…
        </CardContent>
      </Card>
    );
  }
  if (error) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-red-600">
          {error}
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <span>Tag Hierarchy</span>
            <Badge variant="outline">Primary / Secondary / Tertiary</Badge>
          </CardTitle>
          <Button size="sm" onClick={() => setAddOpen({ level: "primary" })} className="gap-2">
            <Plus className="w-4 h-4" /> Add Primary
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {Object.keys(sorted).length === 0 && (
            <p className="text-sm text-gray-500">No tags yet.</p>
          )}

          {Object.entries(sorted).map(([primary, secs]) => {
            const pOpen = !!expandedPrimary[primary];
            return (
              <div key={primary} className="rounded-md border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="p-1 hover:bg-gray-100 rounded"
                      onClick={() =>
                        setExpandedPrimary((s) => ({ ...s, [primary]: !pOpen }))
                      }
                      aria-label={pOpen ? "Collapse" : "Expand"}
                    >
                      {pOpen ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                    <span className="font-medium">{primary}</span>
                    <Badge variant="secondary">Primary</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-2"
                      onClick={() => setAddOpen({ level: "secondary", parent: { primary } })}
                    >
                      <Plus className="w-4 h-4" /> Add Secondary
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-2"
                      onClick={() =>
                        setEditOpen({ level: "primary", currentName: primary })
                      }
                    >
                      <Edit3 className="w-4 h-4" /> Rename
                    </Button>
                  </div>
                </div>

                {pOpen && (
                  <div className="mt-3 pl-6 space-y-2">
                    {Object.keys(secs).length === 0 && (
                      <p className="text-xs text-gray-500">No secondary tags.</p>
                    )}
                    {Object.entries(secs).map(([secondary, tertiaries]) => {
                      const key = `${primary}:${secondary}`;
                      const sOpen = !!expandedSecondary[key];
                      return (
                        <div key={key} className="rounded border p-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                className="p-1 hover:bg-gray-100 rounded"
                                onClick={() =>
                                  setExpandedSecondary((s) => ({
                                    ...s,
                                    [key]: !sOpen,
                                  }))
                                }
                              >
                                {sOpen ? (
                                  <ChevronDown className="w-4 h-4" />
                                ) : (
                                  <ChevronRight className="w-4 h-4" />
                                )}
                              </button>
                              <span>{secondary}</span>
                              <Badge variant="outline">Secondary</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-2"
                                onClick={() =>
                                  setAddOpen({
                                    level: "tertiary",
                                    parent: { primary, secondary },
                                  })
                                }
                              >
                                <Plus className="w-4 h-4" /> Add Tertiary
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-2"
                                onClick={() =>
                                  setEditOpen({
                                    level: "secondary",
                                    currentName: secondary,
                                    parent: { primary },
                                  })
                                }
                              >
                                <Edit3 className="w-4 h-4" /> Rename
                              </Button>
                            </div>
                          </div>

                          {sOpen && (
                            <div className="mt-2 pl-6 flex flex-wrap gap-2">
                              {tertiaries.length === 0 && (
                                <p className="text-xs text-gray-500">No tertiary tags.</p>
                              )}
                              {tertiaries.map((t) => (
                                <div
                                  key={t}
                                  className="flex items-center gap-2 rounded-full border px-2 py-1"
                                >
                                  <span className="text-sm">{t}</span>
                                  <Badge variant="outline">Tertiary</Badge>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-7 px-2 gap-1"
                                    onClick={() =>
                                      setEditOpen({
                                        level: "tertiary",
                                        currentName: t,
                                        parent: { primary, secondary },
                                      })
                                    }
                                  >
                                    <Edit3 className="w-3 h-3" /> Rename
                                  </Button>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      {addOpen && (
        <AddTagModal open={!!addOpen} initial={addOpen} onOpenChange={setAddOpen} />
      )}
      {editOpen && (
        <EditTagModal open={!!editOpen} initial={editOpen} onOpenChange={setEditOpen} />
      )}
    </>
  );
};
