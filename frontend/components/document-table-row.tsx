"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TableCell, TableRow } from "@/components/ui/table"
import { FileText, Calendar, Tag } from "lucide-react"

interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  size: string
}

interface DocumentTableRowProps {
  document: Document
  onEditTags: (document: Document) => void
}

export function DocumentTableRow({ document, onEditTags }: DocumentTableRowProps) {
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
        <div className="flex flex-wrap gap-1">
          {document.tags.map((tag, index) => (
            <Badge key={index} variant="secondary" className="bg-red-50 text-red-700 hover:bg-red-100">
              {tag}
            </Badge>
          ))}
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
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onEditTags(document)}
            className="border-red-200 text-red-700 hover:bg-red-50"
          >
            <Tag className="w-4 h-4 mr-1" />
            Edit Tags
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}