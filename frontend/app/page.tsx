"use client"

import { useState, useMemo, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Upload, Search, Filter, AlertCircle, RefreshCw } from "lucide-react"
import { UploadModal } from "@/components/upload-modal"
import { DocumentDetailsModal } from "@/components/document-details-modal"
import { DocumentTable } from "@/components/document-table"
import { DocumentPagination } from "@/components/document-pagination"
import { UserMenu } from "@/components/auth/user-menu"
import { useDocuments } from "@/hooks/use-documents"
import { useAuth } from "@/contexts/auth-context"
import { Document, apiClient } from "@/lib/api"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function HomePage() {
  // Auth state
  const { user, loading: authLoading } = useAuth()

  // UI state
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState<"name" | "date" | "size">("date")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [detailsDocument, setDetailsDocument] = useState<Document | null>(null)
  const [filterTag, setFilterTag] = useState<string>("")

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 15

  // Debounced search
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("")
  useEffect(() => {
    const t = setTimeout(() => {
      // console.log("[page] 🔎 debounced search ->", searchTerm)
      setDebouncedSearchTerm(searchTerm)
    }, 500)
    return () => clearTimeout(t)
  }, [searchTerm])

  // Reset to page 1 when search or sort changes
  useEffect(() => {
    // console.log("[page] 📄 reset page due to search/sort change")
    setCurrentPage(1)
  }, [debouncedSearchTerm, sortBy, sortOrder])

  // Fetch documents (server-side search + sort)
  const {
    documents,
    pagination,
    loading,
    error,
    refetch,
    createDocument,
    updateDocument,
    deleteDocument,
  } = useDocuments({
    search: debouncedSearchTerm || undefined,
    limit: itemsPerPage,
    offset: (currentPage - 1) * itemsPerPage,
    sortBy,
    sortOrder,
  })

  // Client-side TAG filter only (sorting handled server-side)
  const filteredDocuments = useMemo(() => {
    const filtered = !filterTag ? documents : documents.filter(d => d.tags.includes(filterTag))
    // console.log("[page] 🏷️ tag filter ->", { filterTag, before: documents.length, after: filtered.length })
    return filtered
  }, [documents, filterTag])

  const availableTags = useMemo(() => {
    const tags = new Set<string>()
    documents.forEach((doc) => doc.tags.forEach((tag) => tags.add(tag)))
    return Array.from(tags).sort()
  }, [documents])

  const handleSort = (column: "name" | "date" | "size") => {
    if (sortBy === column) {
      const next = sortOrder === "asc" ? "desc" : "asc"
      // console.log("[page] ↕️ toggle sort order", { column, from: sortOrder, to: next })
      setSortOrder(next)
    } else {
      // console.log("[page] 🔃 change sort column", { from: sortBy, to: column })
      setSortBy(column)
      setSortOrder("asc")
    }
  }

  const handleUploadComplete = async (_newDocument: Document) => {
    try {
      await refetch()
      setIsUploadModalOpen(false)
    } catch (err) {
      console.error("❌ [page] error after upload:", err)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-5xl font-bold text-red-600" style={{ marginLeft: "1rem" }}>
                Clerc.
              </h1>
              <div className="h-6 w-px bg-gray-300 mx-4" />
              <h1 className="text-xl font-bold text-gray-900">Document AI</h1>
            </div>

            <div className="flex items-center gap-4">
              {authLoading ? (
                <div className="w-8 h-8 animate-pulse bg-gray-200 rounded-full" />
              ) : user ? (
                <UserMenu />
              ) : null}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              <div className="flex items-center justify-between">
                <span>Error loading documents: {error}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refetch}
                  className="ml-4 border-red-300 text-red-700 hover:bg-red-100"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Search & Filters */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="w-5 h-5" />
              <span>Search & Filter Documents</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              <div className="flex-1">
                <Input
                  placeholder="Search by document name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full"
                />
              </div>
              <div className="flex flex-col sm:flex-row gap-4">
                <Select
                  value={filterTag || "all-tags"}
                  onValueChange={(value: string) => {
                    const val = value === "all-tags" ? "" : value
                    // console.log("[page] 🏷️ tag select", { value, normalized: val })
                    setFilterTag(val)
                  }}
                >
                  <SelectTrigger className="w-full sm:w-48">
                    <SelectValue placeholder="Filter by tag" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all-tags">All Tags</SelectItem>
                    {availableTags.map((tag) => (
                      <SelectItem key={tag} value={tag}>
                        {tag}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Documents Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span>Document Library</span>
                {loading && <RefreshCw className="w-4 h-4 animate-spin text-gray-500" />}
                <span className="text-sm text-gray-500">
                  {loading
                    ? "Loading..."
                    : pagination
                    ? `Page ${pagination.currentPage} of ${pagination.totalPages} (${pagination.totalItems} total)`
                    : `${filteredDocuments.length} documents`}
                </span>
              </div>

              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Filter className="w-4 h-4" />
                <span>Sort by:</span>
                <Select
                  value={sortBy}
                  onValueChange={(value: "name" | "date" | "size") => {
                    // console.log("[page] 🔃 sort select", { value })
                    setSortBy(value)
                  }}
                  disabled={loading}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="name">Name</SelectItem>
                    <SelectItem value="size">Size</SelectItem>
                  </SelectContent>
                </Select>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const next = sortOrder === "asc" ? "desc" : "asc"
                    // console.log("[page] ↕️ sort order button", { from: sortOrder, to: next })
                    setSortOrder(next)
                  }}
                  disabled={loading}
                >
                  {sortOrder === "asc" ? "Asc" : "Desc"}
                </Button>
              </div>
            </CardTitle>
          </CardHeader>

          <CardContent>
            {loading && documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <RefreshCw className="w-8 h-8 mx-auto mb-4 animate-spin text-gray-300" />
                <p>Loading documents...</p>
              </div>
            ) : (
              <>
                <DocumentTable
                  documents={filteredDocuments}
                  sortBy={sortBy}
                  sortOrder={sortOrder}
                  onSort={handleSort}
                  onViewDetails={setDetailsDocument}
                />

                {pagination && (
                  <div className="mt-6 border-t pt-4">
                    <DocumentPagination
                      currentPage={currentPage}
                      totalPages={pagination.totalPages}
                      totalItems={pagination.totalItems}
                      itemsPerPage={pagination.itemsPerPage}
                      onPageChange={(p) => {
                        // console.log("[page] 📄 page change", { from: currentPage, to: p })
                        setCurrentPage(p)
                      }}
                      loading={loading}
                    />
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </main>

      {/* FABs */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-3">
        <Button
          onClick={() => setIsUploadModalOpen(true)}
          className="h-14 w-14 rounded-full bg-red-600 hover:bg-red-700 shadow-lg"
          size="icon"
          title="Upload Document"
        >
          <Upload className="w-6 h-6" />
        </Button>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadComplete={handleUploadComplete}
      />

      {/* Details Modal */}
      {detailsDocument && (
        <DocumentDetailsModal
          document={detailsDocument}
          onClose={() => setDetailsDocument(null)}
          onConfirm={async (documentId: string, confirmedTagsData: any) => {
            try {
              const documentIdNum = parseInt(documentId)
              await apiClient.updateDocumentTags(documentIdNum, { confirmed_tags: confirmedTagsData })
              await refetch()
            } catch (err) {
              console.error("❌ [page] error updating document tags:", err)
              throw err
            }
          }}
        />
      )}
    </div>
  )
}


