"use client"

import { TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowUpDown } from "lucide-react"

type SortBy = "name" | "date" | "size"
type SortOrder = "asc" | "desc"

interface DocumentTableHeaderProps {
  sortBy: SortBy
  sortOrder: SortOrder
  onSort: (column: SortBy) => void
}

export function DocumentTableHeader({ sortBy, sortOrder, onSort }: DocumentTableHeaderProps) {
  return (
    <TableHeader>
      <TableRow>
        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => onSort("name")}>
          <div className="flex items-center space-x-1">
            <span>Document Name</span>
            <ArrowUpDown className="w-4 h-4" />
          </div>
        </TableHead>
        <TableHead>Tags</TableHead>
        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => onSort("date")}>
          <div className="flex items-center space-x-1">
            <span>Upload Date</span>
            <ArrowUpDown className="w-4 h-4" />
          </div>
        </TableHead>
        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => onSort("size")}>
          <div className="flex items-center space-x-1">
            <span>Size</span>
            <ArrowUpDown className="w-4 h-4" />
          </div>
        </TableHead>
        <TableHead>Actions</TableHead>
      </TableRow>
    </TableHeader>
  )
}