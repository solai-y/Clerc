"use client"

import { TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"

type SortBy = "name" | "date" | "size"
type SortOrder = "asc" | "desc"

interface DocumentTableHeaderProps {
  sortBy: SortBy
  sortOrder: SortOrder
  onSort: (column: SortBy) => void
}

function SortHeaderCell({
  label,
  column,
  active,
  order,
  onClick,
  className,
}: {
  label: string
  column: SortBy
  active: boolean
  order: SortOrder
  onClick: () => void
  className?: string
}) {
  return (
    <TableHead
      className={`cursor-pointer hover:bg-gray-50 select-none ${className || ""}`}
      onClick={() => {
        console.log("[table-header] click", { column, willToggle: active })
        onClick()
      }}
      aria-sort={active ? (order === "asc" ? "ascending" : "descending") : "none"}
      title={active ? `Sorted ${order}` : "Click to sort"}
    >
      <div className="flex items-center space-x-1">
        <span>{label}</span>
        {active ? (
          order === "asc" ? (
            <ArrowUp className="w-4 h-4" />
          ) : (
            <ArrowDown className="w-4 h-4" />
          )
        ) : (
          <ArrowUpDown className="w-4 h-4 opacity-60" />
        )}
      </div>
    </TableHead>
  )
}

export function DocumentTableHeader({ sortBy, sortOrder, onSort }: DocumentTableHeaderProps) {
  return (
    <TableHeader>
      <TableRow>
        <SortHeaderCell
          label="Document Name"
          column="name"
          active={sortBy === "name"}
          order={sortOrder}
          onClick={() => onSort("name")}
          className="w-[280px]"
        />
        <TableHead className="w-[140px]">Primary</TableHead>
        <TableHead className="w-[140px]">Secondary</TableHead>
        <TableHead className="w-[140px]">Tertiary</TableHead>
        <SortHeaderCell
          label="Upload Date"
          column="date"
          active={sortBy === "date"}
          order={sortOrder}
          onClick={() => onSort("date")}
          className="w-[120px]"
        />
        <SortHeaderCell
          label="Size"
          column="size"
          active={sortBy === "size"}
          order={sortOrder}
          onClick={() => onSort("size")}
          className="w-[80px]"
        />
        <TableHead className="w-[130px]">Actions</TableHead>
      </TableRow>
    </TableHeader>
  )
}
