"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiClient, TagHierarchy, AddTagInput, EditTagInput } from "@/lib/api";

type Ctx = {
  loading: boolean;
  error: string | null;
  tree: TagHierarchy;
  refresh: () => Promise<void>;
  addTag: (input: AddTagInput) => Promise<void>;
  updateTag: (input: EditTagInput) => Promise<void>;
  isUnique: (
    layer: "primary" | "secondary" | "tertiary",
    name: string,
    parents?: { primary?: string; secondary?: string }
  ) => boolean;
};

const TagContext = createContext<Ctx | undefined>(undefined);

export const TagProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tree, setTree] = useState<TagHierarchy>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getTagHierarchy(); // includes backend+fallback logic
      setTree(data);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load tags");
      setTree({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const isUnique: Ctx["isUnique"] = (layer, name, parents) => {
    const n = name?.trim();
    if (!n) return false;

    if (layer === "primary") {
      return !Object.keys(tree).some((p) => p.toLowerCase() === n.toLowerCase());
    }

    if (layer === "secondary") {
      const p = parents?.primary;
      if (!p) return true; // parent will be validated elsewhere
      if (!tree[p]) return true;
      return !Object.keys(tree[p]).some((s) => s.toLowerCase() === n.toLowerCase());
    }

    // tertiary
    const p = parents?.primary;
    const s = parents?.secondary;
    if (!p || !s) return true; // parents validated elsewhere
    const arr = tree[p]?.[s] ?? [];
    return !arr.some((t) => t.toLowerCase() === n.toLowerCase());
  };

  const addTag: Ctx["addTag"] = async (input) => {
    // Required parent checks (clear message)
    if (input.layer === "secondary" && !input.parentPrimary) {
      throw new Error("Please select a Primary parent for this Secondary tag.");
    }
    if (input.layer === "tertiary" && (!input.parentPrimary || !input.parentSecondary)) {
      throw new Error("Please select both Primary and Secondary parents for this Tertiary tag.");
    }

    // Uniqueness (scoped)
    const unique = isUnique(input.layer, input.name, {
      primary: input.parentPrimary,
      secondary: input.parentSecondary,
    });
    if (!unique) throw new Error("Tag name already exists in this scope.");

    await apiClient.addTag(input);
    await refresh();
  };

  const updateTag: Ctx["updateTag"] = async (input) => {
    // If only casing changed, allow
    if (input.oldName.trim().toLowerCase() !== input.newName.trim().toLowerCase()) {
      const unique = isUnique(input.layer, input.newName, {
        primary: input.parentPrimary,
        secondary: input.parentSecondary,
      });
      if (!unique) throw new Error("New tag name would duplicate an existing tag in this scope.");
    }
    await apiClient.editTag(input);
    await refresh();
  };

  const value = useMemo<Ctx>(
    () => ({
      loading,
      error,
      tree,
      refresh,
      addTag,
      updateTag,
      isUnique,
    }),
    [loading, error, tree, refresh]
  );

  return <TagContext.Provider value={value}>{children}</TagContext.Provider>;
};

export function useTags() {
  const ctx = useContext(TagContext);
  if (!ctx) throw new Error("useTags must be used inside <TagProvider>");
  return ctx;
}
