"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Progress } from "@/components/ui/progress"
import { 
  FileText, 
  Calendar, 
  Tag, 
  Building, 
  User, 
  Download, 
  ExternalLink,
  Clock,
  CheckCircle,
  AlertCircle,
  Info,
  Bot,
  UserPlus,
  Check,
  X
} from "lucide-react"

interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  size: string
  type: string
  link: string
  company: number | null
  companyName: string | null
  uploaded_by: number | null
  status: string
  modelGeneratedTags: Array<{
    tag: string
    score: number
    isConfirmed: boolean
  }>
  userAddedTags: string[]
}

interface DocumentDetailsModalProps {
  document: Document
  onClose: () => void
}

export function DocumentDetailsModal({ document, onClose }: DocumentDetailsModalProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed':
      case 'completed':
      case 'user_confirmed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />
      case 'failed':
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Info className="w-4 h-4 text-blue-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed':
      case 'completed':
      case 'user_confirmed':
        return 'bg-green-50 text-green-700 border-green-200'
      case 'processing':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200'
      case 'failed':
      case 'error':
        return 'bg-red-50 text-red-700 border-red-200'
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200'
    }
  }

  const handleDownload = () => {
    if (document.link) {
      window.open(document.link, '_blank')
    }
  }

  const handleOpenExternal = () => {
    if (document.link) {
      window.open(document.link, '_blank')
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-[95vw] w-full h-[95vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <FileText className="w-6 h-6" />
            Document Details
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full overflow-hidden">
          {/* Left Column */}
          <div className="space-y-4 overflow-y-auto pr-2">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="font-medium text-sm">Document Name</span>
                    </div>
                    <p className="text-sm bg-gray-50 p-2 rounded border">{document.name}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Info className="w-4 h-4 text-gray-500" />
                        <span className="font-medium text-sm">Document ID</span>
                      </div>
                      <p className="text-xs bg-gray-50 p-2 rounded border font-mono">{document.id}</p>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-500" />
                        <span className="font-medium text-sm">File Type</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {document.type || 'Unknown'}
                      </Badge>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="font-medium text-sm">File Size</span>
                    </div>
                    <p className="text-sm bg-gray-50 p-2 rounded border">{document.size}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Status and Metadata */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Status & Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(document.status)}
                      <span className="font-medium text-sm">Processing Status</span>
                    </div>
                    <Badge className={`text-sm ${getStatusColor(document.status)}`}>
                      {document.status.replace('_', ' ').toUpperCase()}
                    </Badge>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-500" />
                      <span className="font-medium text-sm">Upload Date</span>
                    </div>
                    <p className="text-sm bg-gray-50 p-2 rounded border">
                      {formatDate(document.uploadDate + 'T00:00:00')}
                    </p>
                  </div>

                  {(document.companyName || document.uploaded_by) && (
                    <div className="grid grid-cols-2 gap-3">
                      {document.companyName && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Building className="w-4 h-4 text-gray-500" />
                            <span className="font-medium text-sm">Company</span>
                          </div>
                          <p className="text-sm bg-gray-50 p-2 rounded border">{document.companyName}</p>
                        </div>
                      )}

                      {document.uploaded_by && (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-gray-500" />
                            <span className="font-medium text-sm">Uploaded By</span>
                          </div>
                          <p className="text-sm bg-gray-50 p-2 rounded border">{document.uploaded_by}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Document Access */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Document Access</CardTitle>
              </CardHeader>
              <CardContent>
                {document.link ? (
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">Document Link:</p>
                      <div className="bg-gray-50 p-2 rounded border text-xs font-mono break-all">
                        {document.link}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleDownload}
                        size="sm"
                        className="bg-red-600 hover:bg-red-700"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                      <Button
                        onClick={handleOpenExternal}
                        variant="outline"
                        size="sm"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Open in New Tab
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 italic text-sm">No download link available</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Tags */}
          <div className="space-y-4 overflow-y-auto pr-2">
            {/* Model Generated Tags */}
            <Card className="h-fit">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Bot className="w-5 h-5 text-blue-500" />
                  AI Model Generated Tags
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {document.modelGeneratedTags.length > 0 ? (
                    <div className="space-y-2">
                      {document.modelGeneratedTags.map((modelTag, index) => (
                        <div key={index} className="flex items-center justify-between p-2 border rounded-lg">
                          <div className="flex items-center gap-2 flex-1">
                            <div className="flex items-center gap-1">
                              {modelTag.isConfirmed ? (
                                <Check className="w-4 h-4 text-green-500" />
                              ) : (
                                <X className="w-4 h-4 text-gray-400" />
                              )}
                              <Badge
                                variant={modelTag.isConfirmed ? "default" : "secondary"}
                                className={modelTag.isConfirmed ? 
                                  "bg-green-50 text-green-700 hover:bg-green-100" : 
                                  "bg-gray-50 text-gray-600"
                                }
                              >
                                {modelTag.tag}
                              </Badge>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="text-right">
                              <div className="text-xs text-gray-500">Confidence</div>
                              <div className="text-sm font-medium">
                                {(modelTag.score * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div className="w-16">
                              <Progress 
                                value={modelTag.score * 100} 
                                className="h-2"
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 italic text-sm">No AI-generated tags available</p>
                  )}
                  <div className="text-xs text-gray-500 mt-2 p-2 bg-blue-50 rounded">
                    <div className="flex items-center gap-1 mb-1">
                      <Info className="w-3 h-3" />
                      <span className="font-medium">Legend:</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1">
                        <Check className="w-3 h-3 text-green-500" />
                        <span>User Confirmed</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <X className="w-3 h-3 text-gray-400" />
                        <span>Not Confirmed</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* User Added Tags */}
            <Card className="h-fit">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <UserPlus className="w-5 h-5 text-purple-500" />
                  User Added Tags
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {document.userAddedTags.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {document.userAddedTags.map((userTag, index) => (
                        <Badge
                          key={index}
                          className="bg-purple-50 text-purple-700 hover:bg-purple-100"
                        >
                          {userTag}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 italic text-sm">No user-added tags</p>
                  )}
                  <div className="text-xs text-gray-500 mt-2 p-2 bg-purple-50 rounded">
                    <Info className="w-3 h-3 inline mr-1" />
                    These tags were manually added by users and are automatically confirmed.
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Combined Tags Summary */}
            <Card className="h-fit">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Tag className="w-5 h-5 text-red-500" />
                  Final Tags Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {document.tags.length > 0 ? (
                      document.tags.map((tag, index) => (
                        <Badge
                          key={index}
                          variant="secondary"
                          className="bg-red-50 text-red-700 hover:bg-red-100"
                        >
                          {tag}
                        </Badge>
                      ))
                    ) : (
                      <p className="text-gray-500 italic text-sm">No final tags</p>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 p-2 bg-gray-50 rounded">
                    <Info className="w-3 h-3 inline mr-1" />
                    These are the final confirmed tags (confirmed AI tags + user-added tags) displayed in the main table.
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator className="my-4" />

        <div className="flex justify-end">
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}