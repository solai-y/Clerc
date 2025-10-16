"use client"

import { useEffect, useMemo } from "react"
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

interface DocumentPaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  loading?: boolean
}

export function DocumentPagination({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  loading = false,
}: DocumentPaginationProps) {
  // Guard: nothing to paginate
  if (!totalPages || totalPages <= 1) {
    return null
  }

  // Clamp values just in case
  const safeCurrent = Math.min(Math.max(currentPage || 1, 1), Math.max(totalPages, 1))
  const safePerPage = Math.max(itemsPerPage || 1, 1)
  const safeTotal = Math.max(totalItems || 0, 0)

  // Calculate displayed range
  const startItem = safeTotal === 0 ? 0 : (safeCurrent - 1) * safePerPage + 1
  const endItem = safeTotal === 0 ? 0 : Math.min(safeCurrent * safePerPage, safeTotal)

  // Generate page numbers (with ellipses)
  const pageNumbers = useMemo(() => {
    const delta = 2
    const range: number[] = [1]

    for (let i = Math.max(2, safeCurrent - delta); i <= Math.min(totalPages - 1, safeCurrent + delta); i++) {
      range.push(i)
    }
    if (totalPages > 1) range.push(totalPages)

    const unique = [...new Set(range)].sort((a, b) => a - b)

    const output: Array<number | "ellipsis"> = []
    let prev = 0
    for (const page of unique) {
      if (page - prev > 1) output.push("ellipsis")
      output.push(page)
      prev = page
    }
    return output
  }, [safeCurrent, totalPages])

  useEffect(() => {
    console.log("[Pagination] props changed", {
      currentPage,
      totalPages,
      totalItems,
      itemsPerPage,
      loading,
      computed: { safeCurrent, startItem, endItem, pageNumbers }
    })
  }, [currentPage, totalPages, totalItems, itemsPerPage, loading, pageNumbers, safeCurrent, startItem, endItem])

  const handlePageClick = (page: number) => {
    console.log("[Pagination] click", { page, safeCurrent, totalPages, loading })
    if (!loading && page >= 1 && page <= totalPages && page !== safeCurrent) {
      onPageChange(page)
    }
  }

  return (
    <div className="flex items-center justify-between px-2">
      {/* Results info */}
      <div className="text-sm text-gray-700">
        Showing <span className="font-medium">{startItem}</span> to{" "}
        <span className="font-medium">{endItem}</span> of{" "}
        <span className="font-medium">{safeTotal}</span> documents
      </div>

      {/* Pagination controls */}
      <Pagination>
        <PaginationContent>
          {/* Previous */}
          <PaginationItem>
            <PaginationPrevious
              onClick={() => handlePageClick(safeCurrent - 1)}
              className={`cursor-pointer ${
                safeCurrent <= 1 || loading ? "pointer-events-none opacity-50" : "hover:bg-gray-100"
              }`}
            />
          </PaginationItem>

          {/* Page numbers */}
          {pageNumbers.map((item, idx) => (
            <PaginationItem key={`${item}-${idx}`}>
              {item === "ellipsis" ? (
                <PaginationEllipsis />
              ) : (
                <PaginationLink
                  onClick={() => handlePageClick(item)}
                  isActive={item === safeCurrent}
                  className={`cursor-pointer ${
                    loading ? "pointer-events-none opacity-50" : "hover:bg-gray-100"
                  }`}
                >
                  {item}
                </PaginationLink>
              )}
            </PaginationItem>
          ))}

          {/* Next */}
          <PaginationItem>
            <PaginationNext
              onClick={() => handlePageClick(safeCurrent + 1)}
              className={`cursor-pointer ${
                safeCurrent >= totalPages || loading ? "pointer-events-none opacity-50" : "hover:bg-gray-100"
              }`}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  )
}
