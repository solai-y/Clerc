"use client"

import { useState, useMemo, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Upload, Search, Filter, AlertCircle, RefreshCw, TestTube } from "lucide-react"
import { UploadModal } from "@/components/upload-modal"
import { ConfirmTagsModal } from "@/components/confirm-tags-modal"
import { DocumentDetailsModal } from "@/components/document-details-modal"
import { DocumentTable } from "@/components/document-table"
import { DocumentPagination } from "@/components/document-pagination"
import { useDocuments } from "@/hooks/use-documents"
import { Document, apiClient } from "@/lib/api"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function HomePage() {
  // Local state for UI
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState<"name" | "date" | "size">("date")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [confirmTagsDocument, setConfirmTagsDocument] = useState<Document | null>(null)
  const [detailsDocument, setDetailsDocument] = useState<Document | null>(null)
  const [filterTag, setFilterTag] = useState<string>("")
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 15

  // Debounced search to avoid too many API calls
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState("")
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
    }, 500) // 500ms debounce

    return () => clearTimeout(timer)
  }, [searchTerm])

  // Reset to first page when search changes
  useEffect(() => {
    setCurrentPage(1)
  }, [debouncedSearchTerm])

  // Fetch documents from API
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
    search: debouncedSearchTerm || undefined, // Use debounced search term
    limit: itemsPerPage, // 15 documents per page
    offset: (currentPage - 1) * itemsPerPage, // Calculate offset based on current page
  })

  // Apply client-side filtering for tags and sorting (search is handled server-side)
  const filteredAndSortedDocuments = useMemo(() => {
    const filtered = documents.filter((doc) => {
      const matchesTag = !filterTag || doc.tags.includes(filterTag)
      // Only tag filtering is applied
      return matchesTag
    })

    return filtered.sort((a, b) => {
      let comparison = 0
      switch (sortBy) {
        case "name":
          comparison = a.name.localeCompare(b.name)
          break
        case "date":
          comparison = new Date(a.uploadDate).getTime() - new Date(b.uploadDate).getTime()
          break
        case "size":
          const aSize = Number.parseFloat(a.size)
          const bSize = Number.parseFloat(b.size)
          comparison = aSize - bSize
          break
      }
      return sortOrder === "asc" ? comparison : -comparison
    })
  }, [documents, sortBy, sortOrder, filterTag])

  const availableTags = useMemo(() => {
    const tags = new Set<string>()
    documents.forEach((doc) => doc.tags.forEach((tag) => tags.add(tag)))
    return Array.from(tags).sort()
  }, [documents])


  const handleSort = (column: "name" | "date" | "size") => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(column)
      setSortOrder("asc")
    }
  }

  const handleUploadComplete = async (newDocument: Document) => {
    try {
      // In a real implementation, this would create the document via API
      // For now, we'll just refetch to get the latest data
      await refetch()
      setConfirmTagsDocument(newDocument)
      setIsUploadModalOpen(false)
    } catch (err) {
      console.error('Error after upload:', err)
    }
  }

  const handleConfirmTags = async (
    documentId: string,
    confirmedTags: string[],
    userAddedTags: string[]
  ) => {
    try {
      console.log('✅ Confirming document tags:', {
        documentId,
        confirmedTags,
        userAddedTags,
        totalTags: confirmedTags.length + userAddedTags.length
      })

      const documentIdNum = parseInt(documentId)
      
      // Update the processed document with confirmed tags
      // (processed_documents entry should already exist from upload flow)
      await apiClient.updateDocumentTags(documentIdNum, {
        confirmed_tags: confirmedTags,
        user_added_labels: userAddedTags
      })
      
      console.log('✅ Successfully updated document tags')
      
      // Refresh the document list to show updated tags
      await refetch()
      setConfirmTagsDocument(null)
      
    } catch (err) {
      console.error('❌ Error updating document tags:', err)
      // If the processed document doesn't exist, try to create it first (fallback)
      if (err instanceof Error && err.message.includes('No processed document found')) {
        console.log('🔄 Processed document not found, creating it first...')
        try {
          // Create processed document entry as fallback
          const mockAITags = confirmTagsDocument?.modelGeneratedTags.map(tag => ({
            tag: tag.tag,
            score: tag.score
          })) || []
          
          await apiClient.createProcessedDocument({
            document_id: documentIdNum,
            suggested_tags: mockAITags,
            threshold_pct: 60
          })
          
          // Now update with confirmed tags
          await apiClient.updateDocumentTags(documentIdNum, {
            confirmed_tags: confirmedTags,
            user_added_labels: userAddedTags
          })
          
          console.log('✅ Created processed document and updated tags (fallback)')
          await refetch()
          setConfirmTagsDocument(null)
          
        } catch (fallbackError) {
          console.error('❌ Fallback also failed:', fallbackError)
          throw fallbackError
        }
      } else {
        throw err
      }
    }
  }

  // Create mock processed document for testing
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 B"
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  }

  const generateMockAITags = (fileName: string) => {
    // Generate AI tags based on filename
    const name = fileName.toLowerCase()
    const tags: { tag: string; score: number }[] = []

    // Document type detection
    if (name.includes("financial") || name.includes("finance")) {
      tags.push({ tag: "Financial Report", score: 0.92 })
    }
    if (name.includes("risk")) {
      tags.push({ tag: "Risk Management", score: 0.87 })
    }
    if (name.includes("investment")) {
      tags.push({ tag: "Investment", score: 0.84 })
    }
    if (name.includes("market")) {
      tags.push({ tag: "Market Analysis", score: 0.81 })
    }
    if (name.includes("compliance")) {
      tags.push({ tag: "Compliance", score: 0.88 })
    }
    if (name.includes("contract")) {
      tags.push({ tag: "Contract", score: 0.95 })
    }
    if (name.includes("legal")) {
      tags.push({ tag: "Legal", score: 0.89 })
    }
    if (name.includes("invoice")) {
      tags.push({ tag: "Invoice", score: 0.94 })
    }
    if (name.includes("report")) {
      tags.push({ tag: "Report", score: 0.85 })
    }
    
    // Time period detection
    if (name.includes("quarterly") || name.includes("q1") || name.includes("q2") || name.includes("q3") || name.includes("q4")) {
      tags.push({ tag: "Quarterly", score: 0.78 })
    }
    if (name.includes("annual")) {
      tags.push({ tag: "Annual", score: 0.75 })
    }

    // Add some default tags if none found
    if (tags.length === 0) {
      tags.push({ tag: "Document", score: 0.70 })
      tags.push({ tag: "Unclassified", score: 0.60 })
    }

    return tags
  }

  const createMockProcessedDocument = (): Document => {
    // Create various test scenarios
    const testScenarios = [
      {
        name: "Test_Invoice_2024_Q1.pdf",
        tags: [
          { tag: "invoice", score: 0.92 },
          { tag: "financial", score: 0.87 },
          { tag: "business", score: 0.74 },
          { tag: "payment", score: 0.68 },
          { tag: "accounting", score: 0.61 }
        ]
      },
      {
        name: "Contract_Agreement_Legal.pdf", 
        tags: [
          { tag: "contract", score: 0.95 },
          { tag: "legal", score: 0.89 },
          { tag: "agreement", score: 0.82 },
          { tag: "terms", score: 0.71 },
          { tag: "business", score: 0.65 }
        ]
      },
      {
        name: "Marketing_Report_Q4.pdf",
        tags: [
          { tag: "marketing", score: 0.91 },
          { tag: "report", score: 0.88 },
          { tag: "analytics", score: 0.76 },
          { tag: "quarterly", score: 0.69 },
          { tag: "strategy", score: 0.62 }
        ]
      }
    ]

    // Randomly select a scenario
    const scenario = testScenarios[Math.floor(Math.random() * testScenarios.length)]

    return {
      id: Math.floor(Date.now() / 1000).toString(), // Generate integer-like ID
      name: scenario.name,
      uploadDate: new Date().toISOString().split('T')[0],
      tags: [], // Will be populated based on confirmed tags
      size: `${(Math.random() * 3 + 1).toFixed(1)} MB`,
      type: "PDF",
      link: `/documents/${scenario.name}`,
      company: 1,
      companyName: "Test Company Inc.",
      uploaded_by: 1,
      status: "pending_review",
      modelGeneratedTags: scenario.tags.map(tag => ({
        tag: tag.tag,
        score: tag.score,
        isConfirmed: true // AI tags are selected by default
      })),
      userAddedTags: [] // Initially empty
    }
  }

  const handleTestProcessedDocument = async () => {
    try {
      // Get a real unprocessed document from the database
      const response = await apiClient.getUnprocessedDocuments(1)
      
      if (response.count === 0) {
        alert('⚠️ No unprocessed documents found!\n\nAll raw documents have already been processed.')
        return
      }
      
      const rawDoc = response.unprocessed_documents[0]
      
      // Transform raw document into a format suitable for tag confirmation
      // Generate mock AI tags for this real document
      const mockAITags = generateMockAITags(rawDoc.document_name)
      
      const testDoc: Document = {
        id: rawDoc.document_id.toString(),
        name: rawDoc.document_name,
        uploadDate: rawDoc.upload_date?.split('T')[0] || new Date().toISOString().split('T')[0],
        tags: [], // Will be populated based on confirmed tags
        size: rawDoc.file_size ? formatFileSize(rawDoc.file_size) : 'Unknown',
        type: rawDoc.document_type || 'PDF',
        link: rawDoc.link || '',
        company: rawDoc.company,
        companyName: null, // We don't have company name from raw document
        uploaded_by: rawDoc.uploaded_by,
        status: "pending_review",
        modelGeneratedTags: mockAITags.map(tag => ({
          tag: tag.tag,
          score: tag.score,
          isConfirmed: true // AI tags are selected by default
        })),
        userAddedTags: [] // Initially empty
      }
      
      setConfirmTagsDocument(testDoc)
      
    } catch (error) {
      console.error('Failed to get unprocessed document:', error)
      alert('❌ Failed to get unprocessed document!\n\nError: ' + (error as Error).message)
    }
  }


  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-5xl font-bold text-red-600" style={{ marginLeft: '1rem' }}>Clerc.</h1>
                <div className="h-6 w-px bg-gray-300 mx-4"></div>
                <h1 className="text-xl font-bold text-gray-900">Document AI</h1>
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


        {/* Search and Filters */}
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
                  placeholder="Search by document name or tags..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full"
                />
              </div>
              <div className="flex flex-col sm:flex-row gap-4">
                <Select
                  value={filterTag || "all-tags"}
                  onValueChange={(value: string) => {
                    const newValue = value === "all-tags" ? "" : value
                    setFilterTag(newValue)
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
                  {loading ? (
                    "Loading..."
                  ) : pagination ? (
                    `Page ${pagination.currentPage} of ${pagination.totalPages} (${pagination.totalItems} total)`
                  ) : (
                    `${filteredAndSortedDocuments.length} documents`
                  )}
                </span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Filter className="w-4 h-4" />
                <span>Sort by:</span>
                <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)} disabled={loading}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="name">Name</SelectItem>
                    <SelectItem value="size">Size</SelectItem>
                  </SelectContent>
                </Select>
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
                  documents={filteredAndSortedDocuments}
                  sortBy={sortBy}
                  sortOrder={sortOrder}
                  onSort={handleSort}
                  onEditTags={setConfirmTagsDocument}
                  onViewDetails={setDetailsDocument}
                />
                
                {/* Pagination */}
                {pagination && (
                  <div className="mt-6 border-t pt-4">
                    <DocumentPagination
                      currentPage={currentPage}
                      totalPages={pagination.totalPages}
                      totalItems={pagination.totalItems}
                      itemsPerPage={pagination.itemsPerPage}
                      onPageChange={setCurrentPage}
                      loading={loading}
                    />
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-3">
        {/* Test Processed Document Button */}
        <Button
          onClick={handleTestProcessedDocument}
          className="h-12 w-12 rounded-full bg-blue-600 hover:bg-blue-700 shadow-lg"
          size="icon"
          title="Test Tag Confirmation Flow"
        >
          <TestTube className="w-5 h-5" />
        </Button>
        
        {/* Upload Button */}
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

      {/* Confirm Tags Modal */}
      {confirmTagsDocument && (
        <ConfirmTagsModal
          document={confirmTagsDocument}
          onConfirm={handleConfirmTags}
          onClose={() => setConfirmTagsDocument(null)}
        />
      )}

      {/* Document Details Modal */}
      {detailsDocument && (
        <DocumentDetailsModal
          document={detailsDocument}
          onClose={() => setDetailsDocument(null)}
        />
      )}
    </div>
  )
}
