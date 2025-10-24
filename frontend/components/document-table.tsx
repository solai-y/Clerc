"use client"

import { useEffect } from "react"
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

export function DocumentTable({
  documents,
  sortBy,
  sortOrder,
  onSort,
  onViewDetails
}: DocumentTableProps) {
  // Debug whenever inputs change
  useEffect(() => {
    // console.log("[DocumentTable] render", {
    //   rows: documents.length,
    //   sortBy,
    //   sortOrder,
    //   sample: documents.slice(0, 3).map(d => ({
    //     id: d.id,
    //     name: d.name,
    //     uploadDate: d.uploadDate,
    //     size: d.size
    //   }))
    // })
  }, [documents, sortBy, sortOrder])

  if (documents.length === 0) {
    // console.log("[DocumentTable] empty state (no rows to render)")
    return (
      <div className="text-center py-8 text-gray-500">
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No documents found matching your criteria.</p>
      </div>
    )
  }

  return (
    <div className="w-full overflow-x-auto">
      <Table className="table-fixed">
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
    </div>
  )
}
