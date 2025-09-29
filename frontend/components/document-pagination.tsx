"use client"

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
  // Don't show pagination if there's only one page or less
  if (totalPages <= 1) {
    return null
  }

  // Calculate the range of items being displayed
  const startItem = (currentPage - 1) * itemsPerPage + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  // Generate page numbers to display
  const getPageNumbers = () => {
    const delta = 2 // Number of pages to show around current page
    const range = []
    const rangeWithDots = []

    // Always include first page
    range.push(1)

    // Add pages around current page
    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i)
    }

    // Always include last page if it's not the first page
    if (totalPages > 1) {
      range.push(totalPages)
    }

    // Remove duplicates and sort
    const uniqueRange = [...new Set(range)].sort((a, b) => a - b)

    // Add ellipsis where there are gaps
    let prev = 0
    for (const page of uniqueRange) {
      if (page - prev > 1) {
        rangeWithDots.push('ellipsis')
      }
      rangeWithDots.push(page)
      prev = page
    }

    return rangeWithDots
  }

  const pageNumbers = getPageNumbers()

  const handlePageClick = (page: number) => {
    if (!loading && page >= 1 && page <= totalPages && page !== currentPage) {
      onPageChange(page)
    }
  }

  return (
    <div className="flex items-center justify-between px-2">
      {/* Results info */}
      <div className="text-sm text-gray-700">
        Showing <span className="font-medium">{startItem}</span> to{" "}
        <span className="font-medium">{endItem}</span> of{" "}
        <span className="font-medium">{totalItems}</span> documents
      </div>

      {/* Pagination controls */}
      <Pagination>
        <PaginationContent>
          {/* Previous button */}
          <PaginationItem>
            <PaginationPrevious
              onClick={() => handlePageClick(currentPage - 1)}
              className={`cursor-pointer ${
                currentPage <= 1 || loading 
                  ? 'pointer-events-none opacity-50' 
                  : 'hover:bg-gray-100'
              }`}
            />
          </PaginationItem>

          {/* Page numbers */}
          {pageNumbers.map((item, index) => (
            <PaginationItem key={index}>
              {item === 'ellipsis' ? (
                <PaginationEllipsis />
              ) : (
                <PaginationLink
                  onClick={() => handlePageClick(item as number)}
                  isActive={item === currentPage}
                  className={`cursor-pointer ${
                    loading 
                      ? 'pointer-events-none opacity-50' 
                      : 'hover:bg-gray-100'
                  }`}
                >
                  {item}
                </PaginationLink>
              )}
            </PaginationItem>
          ))}

          {/* Next button */}
          <PaginationItem>
            <PaginationNext
              onClick={() => handlePageClick(currentPage + 1)}
              className={`cursor-pointer ${
                currentPage >= totalPages || loading 
                  ? 'pointer-events-none opacity-50' 
                  : 'hover:bg-gray-100'
              }`}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  )
}