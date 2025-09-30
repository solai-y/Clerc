"use client"

import { Table, TableBody } from "@/components/ui/table"
import { FileText } from "lucide-react"
import { DocumentTableHeader } from "@/components/document-table-header"
import { DocumentTableRow } from "@/components/document-table-row"

import { Document } from "@/lib/api"

type SortBy = "name" | "date" | "size"
type SortOrder = "asc" | "desc"

interface DocumentTableProps {
  documents: Document[]
  sortBy: SortBy
  sortOrder: SortOrder
  onSort: (column: SortBy) => void
  onViewDetails: (document: Document) => void
}

export function DocumentTable({ documents, sortBy, sortOrder, onSort, onViewDetails }: DocumentTableProps) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No documents found matching your criteria.</p>
      </div>
    )
  }

  return (
    <Table>
      <DocumentTableHeader sortBy={sortBy} sortOrder={sortOrder} onSort={onSort} />
      <TableBody>
        {documents.map((document) => (
          <DocumentTableRow
            key={document.id}
            document={document}
            onViewDetails={onViewDetails}
          />
        ))}
      </TableBody>
    </Table>
  )
}