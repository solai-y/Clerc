"use client"

import { useState, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Upload, Search, Filter, ArrowUpDown, FileText, Calendar, Tag } from "lucide-react"
import { UploadModal } from "@/components/upload-modal"
import { ConfirmTagsModal } from "@/components/confirm-tags-modal"

interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  subtags: { [tagId: string]: string[] } // Map of tag to its subtags
  size: string
}

const mockDocuments: Document[] = [
  {
    id: "1",
    name: "Q3_Financial_Report.pdf",
    uploadDate: "2024-01-15",
    tags: ["Financial Report", "Quarterly", "Revenue"],
    subtags: {
      "Financial Report": ["Income Statement", "Balance Sheet"],
      Quarterly: ["Q3 2024"],
      Revenue: ["Operating Revenue", "Non-Operating Revenue"],
    },
    size: "2.4 MB",
  },
  {
    id: "2",
    name: "Risk_Assessment_2024.docx",
    uploadDate: "2024-01-14",
    tags: ["Risk Management", "Assessment", "Compliance"],
    subtags: {
      "Risk Management": ["Credit Risk", "Market Risk", "Operational Risk"],
      Assessment: ["Annual Assessment"],
      Compliance: ["Regulatory Compliance", "Internal Compliance"],
    },
    size: "1.8 MB",
  },
  {
    id: "3",
    name: "Investment_Strategy.pdf",
    uploadDate: "2024-01-13",
    tags: ["Investment", "Strategy", "Portfolio"],
    subtags: {
      Investment: ["Equity Investment", "Bond Investment"],
      Strategy: ["Long-term Strategy", "Short-term Strategy"],
      Portfolio: ["Diversified Portfolio"],
    },
    size: "3.1 MB",
  },
  {
    id: "4",
    name: "Market_Analysis_Jan.xlsx",
    uploadDate: "2024-01-12",
    tags: ["Market Analysis", "Data", "Trends"],
    subtags: {
      "Market Analysis": ["Technical Analysis", "Fundamental Analysis"],
      Data: ["Historical Data", "Real-time Data"],
      Trends: ["Market Trends", "Industry Trends"],
    },
    size: "5.2 MB",
  },
  {
    id: "5",
    name: "Compliance_Checklist.pdf",
    uploadDate: "2024-01-11",
    tags: ["Compliance", "Regulatory", "Checklist"],
    subtags: {
      Compliance: ["SOX Compliance", "Basel III"],
      Regulatory: ["SEC Requirements", "FINRA Rules"],
      Checklist: ["Monthly Checklist", "Annual Checklist"],
    },
    size: "892 KB",
  },
]

export default function HomePage() {
  const [documents, setDocuments] = useState<Document[]>(mockDocuments)
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState<"name" | "date" | "size">("date")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [confirmTagsDocument, setConfirmTagsDocument] = useState<Document | null>(null)
  const [filterTag, setFilterTag] = useState<string>("")
  const [filterSubtag, setFilterSubtag] = useState<string>("")

  const filteredAndSortedDocuments = useMemo(() => {
    const filtered = documents.filter((doc) => {
      const matchesSearch =
        doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.tags.some((tag) => tag.toLowerCase().includes(searchTerm.toLowerCase())) ||
        Object.values(doc.subtags)
          .flat()
          .some((subtag) => subtag.toLowerCase().includes(searchTerm.toLowerCase()))

      const matchesTag = !filterTag || doc.tags.includes(filterTag)
      const matchesSubtag = !filterSubtag || Object.values(doc.subtags).flat().includes(filterSubtag)

      return matchesSearch && matchesTag && matchesSubtag
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
  }, [documents, searchTerm, sortBy, sortOrder, filterTag, filterSubtag])

  const availableTags = useMemo(() => {
    const tags = new Set<string>()
    documents.forEach((doc) => doc.tags.forEach((tag) => tags.add(tag)))
    return Array.from(tags).sort()
  }, [documents])

  const availableSubtags = useMemo(() => {
    if (!filterTag) return []
    const subtags = new Set<string>()
    documents.forEach((doc) => {
      if (doc.tags.includes(filterTag) && doc.subtags[filterTag]) {
        doc.subtags[filterTag].forEach((subtag) => subtags.add(subtag))
      }
    })
    return Array.from(subtags).sort()
  }, [documents, filterTag])

  const handleSort = (column: "name" | "date" | "size") => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(column)
      setSortOrder("asc")
    }
  }

  const handleUploadComplete = (newDocument: Document) => {
    setDocuments((prev) => [newDocument, ...prev])
    setConfirmTagsDocument(newDocument)
    setIsUploadModalOpen(false)
  }

  const handleConfirmTags = (
    documentId: string,
    confirmedTags: string[],
    confirmedSubtags: { [tagId: string]: string[] },
  ) => {
    setDocuments((prev) =>
      prev.map((doc) => (doc.id === documentId ? { ...doc, tags: confirmedTags, subtags: confirmedSubtags } : doc)),
    )
    setConfirmTagsDocument(null)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <img src="/nomura-logo.png" alt="Nomura Holdings" className="h-8 w-auto" />
              <div className="h-6 w-px bg-gray-300"></div>
              <h1 className="text-xl font-bold text-gray-900">Document AI</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
                  placeholder="Search by document name, tags, or subtags..."
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
                    setFilterSubtag("") // Reset subtag when tag changes
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

                {filterTag && (
                  <Select
                    value={filterSubtag || "all-subtags"}
                    onValueChange={(value: string) => {
                      const newValue = value === "all-subtags" ? "" : value
                      setFilterSubtag(newValue)
                    }}
                  >
                    <SelectTrigger className="w-full sm:w-48">
                      <SelectValue placeholder="Filter by subtag" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all-subtags">All Subtags</SelectItem>
                      {availableSubtags.map((subtag) => (
                        <SelectItem key={subtag} value={subtag}>
                          {subtag}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Documents Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Document Library ({filteredAndSortedDocuments.length})</span>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Filter className="w-4 h-4" />
                <span>Sort by:</span>
                <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort("name")}>
                    <div className="flex items-center space-x-1">
                      <span>Document Name</span>
                      <ArrowUpDown className="w-4 h-4" />
                    </div>
                  </TableHead>
                  <TableHead>Tags</TableHead>
                  <TableHead>Subtags</TableHead>
                  <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort("date")}>
                    <div className="flex items-center space-x-1">
                      <span>Upload Date</span>
                      <ArrowUpDown className="w-4 h-4" />
                    </div>
                  </TableHead>
                  <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort("size")}>
                    <div className="flex items-center space-x-1">
                      <span>Size</span>
                      <ArrowUpDown className="w-4 h-4" />
                    </div>
                  </TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedDocuments.map((doc) => (
                  <TableRow key={doc.id} className="hover:bg-gray-50">
                    <TableCell className="font-medium">
                      <div className="flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-gray-500" />
                        <span>{doc.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {doc.tags.map((tag, index) => (
                          <Badge key={index} variant="secondary" className="bg-red-50 text-red-700 hover:bg-red-100">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(doc.subtags).map(([tag, subtags]) =>
                          subtags.map((subtag, index) => (
                            <Badge
                              key={`${tag}-${index}`}
                              variant="outline"
                              className="text-xs border-red-200 text-red-600"
                            >
                              {subtag}
                            </Badge>
                          )),
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1 text-gray-600">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDate(doc.uploadDate)}</span>
                      </div>
                    </TableCell>
                    <TableCell>{doc.size}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setConfirmTagsDocument(doc)}
                          className="border-red-200 text-red-700 hover:bg-red-50"
                        >
                          <Tag className="w-4 h-4 mr-1" />
                          Edit Tags
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {filteredAndSortedDocuments.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No documents found matching your criteria.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Floating Upload Button */}
      <Button
        onClick={() => setIsUploadModalOpen(true)}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-red-600 hover:bg-red-700 shadow-lg"
        size="icon"
      >
        <Upload className="w-6 h-6" />
      </Button>

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
    </div>
  )
}
