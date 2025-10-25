"use client";

import React, { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Edit3, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTags } from "@/contexts/tag-context";
import { AddTagModal, EditTagModal } from "@/components/tag-modals";

/**
 * Visual-only styling:
 * - Distinct colors per level (Primary=sky, Secondary=violet, Tertiary=amber)
 * - Softer cards, dividers, spacing
 * - ZERO logic changes
 */
export const TagTree: React.FC = () => {
  const { tree, loading, error } = useTags();

  const [expandedPrimary, setExpandedPrimary] = useState<Record<string, boolean>>({});
  const [expandedSecondary, setExpandedSecondary] = useState<Record<string, boolean>>({});

  const [addOpen, setAddOpen] = useState<
    | null
    | { level: "primary" | "secondary" | "tertiary"; parent?: { primary?: string; secondary?: string } }
  >(null);

  const [editOpen, setEditOpen] = useState<
    | null
    | { level: "primary" | "secondary" | "tertiary"; currentName: string; parent?: { primary?: string; secondary?: string } }
  >(null);

  const sorted = useMemo(() => {
    const clone: typeof tree = {};
    Object.keys(tree)
      .sort()
      .forEach((p) => {
        clone[p] = {};
        Object.keys(tree[p])
          .sort()
          .forEach((s) => {
            clone[p][s] = [...tree[p][s]].sort();
          });
      });
    return clone;
  }, [tree]);

  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          Loading tag hierarchy…
        </CardContent>
      </Card>
    );
  }
  if (error) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-destructive">
          {error}
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="shadow-sm border-gray-200">
        <CardHeader className="flex-row items-center justify-between border-b bg-white/60 backdrop-blur">
          <CardTitle className="flex items-center gap-3">
            <span className="text-xl font-semibold">Tag Hierarchy</span>
            <span className="hidden md:flex items-center gap-2">
              <Badge className="bg-sky-100 text-sky-800 border-sky-200">Primary</Badge>
              <Badge className="bg-violet-100 text-violet-800 border-violet-200">Secondary</Badge>
              <Badge className="bg-amber-100 text-amber-800 border-amber-200">Tertiary</Badge>
            </span>
          </CardTitle>

          <Button
            size="sm"
            onClick={() => setAddOpen({ level: "primary" })}
            className="gap-2 rounded-full shadow-sm"
          >
            <Plus className="w-4 h-4" /> Add Primary
          </Button>
        </CardHeader>

        <CardContent className="space-y-4 py-6">
          {Object.keys(sorted).length === 0 && (
            <p className="text-sm text-muted-foreground">No tags yet.</p>
          )}

          {Object.entries(sorted).map(([primary, secs]) => {
            const pOpen = !!expandedPrimary[primary];
            return (
              <div key={primary} className="rounded-lg border bg-white/70 backdrop-blur-sm">
                <div className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-3">
                    <button
                      className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                      onClick={() =>
                        setExpandedPrimary((s) => ({ ...s, [primary]: !pOpen }))
                      }
                      aria-label={pOpen ? "Collapse" : "Expand"}
                    >
                      {pOpen ? (
                        <ChevronDown className="w-4 h-4 text-gray-600" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-600" />
                      )}
                    </button>
                    <span className="font-medium text-gray-900">{primary}</span>
                    <Badge className="bg-sky-100 text-sky-800 border-sky-200">Primary</Badge>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-2 rounded-full hover:bg-sky-50"
                      onClick={() => setAddOpen({ level: "secondary", parent: { primary } })}
                    >
                      <Plus className="w-4 h-4" /> Add Secondary
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-2 rounded-full hover:bg-sky-50"
                      onClick={() =>
                        setEditOpen({ level: "primary", currentName: primary })
                      }
                    >
                      <Edit3 className="w-4 h-4" /> Rename
                    </Button>
                  </div>
                </div>

                {pOpen && (
                  <div className="border-t px-4 py-3 space-y-3">
                    {Object.keys(secs).length === 0 && (
                      <p className="text-xs text-muted-foreground pl-7">No secondary tags.</p>
                    )}

                    {Object.entries(secs).map(([secondary, tertiaries]) => {
                      const key = `${primary}:${secondary}`;
                      const sOpen = !!expandedSecondary[key];

                      return (
                        <div key={key} className="rounded-lg border bg-gray-50/70">
                          <div className="flex items-center justify-between px-3 py-2">
                            <div className="flex items-center gap-3">
                              <button
                                className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                                onClick={() =>
                                  setExpandedSecondary((s) => ({ ...s, [key]: !sOpen }))
                                }
                              >
                                {sOpen ? (
                                  <ChevronDown className="w-4 h-4 text-gray-600" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 text-gray-600" />
                                )}
                              </button>
                              <span className="text-gray-900">{secondary}</span>
                              <Badge className="bg-violet-100 text-violet-800 border-violet-200">
                                Secondary
                              </Badge>
                            </div>

                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                className="gap-2 rounded-full hover:bg-violet-50"
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
                                className="gap-2 rounded-full hover:bg-violet-50"
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
                            <div className="border-t px-4 py-3 pl-9 flex flex-wrap gap-2">
                              {tertiaries.length === 0 && (
                                <p className="text-xs text-muted-foreground">No tertiary tags.</p>
                              )}
                              {tertiaries.map((t) => (
                                <div
                                  key={t}
                                  className="flex items-center gap-2 rounded-full border bg-white px-3 py-1 shadow-sm"
                                >
                                  <span className="text-sm text-gray-900">{t}</span>
                                  <Badge className="bg-amber-100 text-amber-800 border-amber-200">
                                    Tertiary
                                  </Badge>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-7 px-2 gap-1 text-gray-600 hover:bg-amber-50"
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
