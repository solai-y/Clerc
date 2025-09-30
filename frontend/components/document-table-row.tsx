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
    primaryTag: document.primaryTag,
    secondaryTag: document.secondaryTag,
    tertiaryTag: document.tertiaryTag,
    userAddedTags: document.userAddedTags,
    hasHierarchicalTags: !!(document.primaryTag || document.secondaryTag || document.tertiaryTag)
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
      <TableCell className="font-medium">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-gray-500" />
          <span>{document.name}</span>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex flex-col gap-1">
          {/* Primary Tag */}
          {document.primaryTag && (
            <div className="flex items-center gap-1">
              <Badge variant="secondary" className="bg-blue-50 text-blue-800 hover:bg-blue-100">
                <span className="w-2 h-2 rounded-full bg-blue-500 mr-1"></span>
                {document.primaryTag.tag}
              </Badge>
            </div>
          )}

          {/* Secondary Tag */}
          {document.secondaryTag && (
            <div className="flex items-center gap-1">
              <Badge variant="secondary" className="bg-green-50 text-green-800 hover:bg-green-100">
                <span className="w-2 h-2 rounded-full bg-green-500 mr-1"></span>
                {document.secondaryTag.tag}
              </Badge>
            </div>
          )}

          {/* Tertiary Tag */}
          {document.tertiaryTag && (
            <div className="flex items-center gap-1">
              <Badge variant="secondary" className="bg-orange-50 text-orange-800 hover:bg-orange-100">
                <span className="w-2 h-2 rounded-full bg-orange-500 mr-1"></span>
                {document.tertiaryTag.tag}
              </Badge>
            </div>
          )}

          {/* No tags message if none found */}
          {!document.primaryTag && !document.secondaryTag && !document.tertiaryTag && (!document.userAddedTags || document.userAddedTags.length === 0) && (
            <div className="text-gray-400 italic text-sm">No tags assigned</div>
          )}

          {/* User Added Tags */}
          {document.userAddedTags && document.userAddedTags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {document.userAddedTags.map((tag, index) => (
                <Badge key={`user-${index}`} variant="outline" className="bg-yellow-50 text-yellow-800 border-yellow-200">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center space-x-1 text-gray-600">
          <Calendar className="w-4 h-4" />
          <span>{formatDate(document.uploadDate)}</span>
        </div>
      </TableCell>
      <TableCell>{document.size}</TableCell>
      <TableCell>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onViewDetails(document)}
          className="border-blue-200 text-blue-700 hover:bg-blue-50"
        >
          <Eye className="w-4 h-4 mr-1" />
          View Details
        </Button>
      </TableCell>
    </TableRow>
  )
}