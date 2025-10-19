"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TableCell, TableRow } from "@/components/ui/table"
import { FileText, Calendar, Eye } from "lucide-react"

import { Document } from "@/lib/api"

interface DocumentTableRowProps {
  document: Document
  onViewDetails: (document: Document) => void
}

export function DocumentTableRow({ document, onViewDetails }: DocumentTableRowProps) {
  console.log('🏷️ [Document Row] Rendering document tags:', {
    documentId: document.id,
    documentName: document.name,
    tags: document.tags,
    primaryTags: document.primaryTags,
    secondaryTags: document.secondaryTags,
    tertiaryTags: document.tertiaryTags,
    userAddedTags: document.userAddedTags,
    hasHierarchicalTags: !!(document.primaryTags?.length || document.secondaryTags?.length || document.tertiaryTags?.length)
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <TableRow className="hover:bg-gray-50">
      <TableCell className="font-medium w-[280px]">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
          <span className="truncate">{document.name}</span>
        </div>
      </TableCell>

      {/* Primary Tags Column */}
      <TableCell className="w-[140px]">
        <div className="flex flex-wrap gap-1">
          {document.primaryTags && document.primaryTags.length > 0 ? (
            document.primaryTags.map((tagData, index) => (
              <Badge
                key={`primary-${index}`}
                variant="secondary"
                className="bg-blue-50 text-blue-800 hover:bg-blue-100 text-xs"
              >
                {tagData.tag}
              </Badge>
            ))
          ) : (
            <span className="text-gray-400 italic text-xs">-</span>
          )}
        </div>
      </TableCell>

      {/* Secondary Tags Column */}
      <TableCell className="w-[140px]">
        <div className="flex flex-wrap gap-1">
          {document.secondaryTags && document.secondaryTags.length > 0 ? (
            document.secondaryTags.map((tagData, index) => (
              <Badge
                key={`secondary-${index}`}
                variant="secondary"
                className="bg-green-50 text-green-800 hover:bg-green-100 text-xs"
              >
                {tagData.tag}
              </Badge>
            ))
          ) : (
            <span className="text-gray-400 italic text-xs">-</span>
          )}
        </div>
      </TableCell>

      {/* Tertiary Tags Column */}
      <TableCell className="w-[140px]">
        <div className="flex flex-wrap gap-1">
          {document.tertiaryTags && document.tertiaryTags.length > 0 ? (
            document.tertiaryTags.map((tagData, index) => (
              <Badge
                key={`tertiary-${index}`}
                variant="secondary"
                className="bg-orange-50 text-orange-800 hover:bg-orange-100 text-xs"
              >
                {tagData.tag}
              </Badge>
            ))
          ) : (
            <span className="text-gray-400 italic text-xs">-</span>
          )}
        </div>
      </TableCell>

      <TableCell className="w-[120px]">
        <div className="flex items-center space-x-1 text-gray-600 text-sm">
          <Calendar className="w-4 h-4" />
          <span>{formatDate(document.uploadDate)}</span>
        </div>
      </TableCell>
      <TableCell className="w-[80px] text-sm">{document.size}</TableCell>
      <TableCell className="w-[130px]">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onViewDetails(document)}
          className="border-blue-200 text-blue-700 hover:bg-blue-50"
        >
          <Eye className="w-4 h-4 mr-1" />
          Details
        </Button>
      </TableCell>
    </TableRow>
  )
}