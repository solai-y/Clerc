"use client";

import React from "react";
import { TagTree } from "@/components/tag-tree";
import { TagProvider } from "@/contexts/tag-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

/**
 * Dedicated page to display / manage the full tag hierarchy.
 * - Expand / collapse sections
 * - Add / Edit tags
 * - Future-proofed so this same page is used for both browse + edit.
 */
export default function TagsManagerPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-blue-600" />
            Tag Manager
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-600">
          View the complete tag taxonomy and add or edit tags as your business needs evolve.
        </CardContent>
      </Card>

      <TagProvider>
        <TagTree />
      </TagProvider>
    </div>
  );
}
