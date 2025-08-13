"use client"

import type React from "react"

import { useState, useCallback, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'

interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  subtags: { [tagId: string]: string[] }
  size: string
}

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUploadComplete: (document: Document) => void
}

export function UploadModal({ isOpen, onClose, onUploadComplete }: UploadModalProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  const uploadToS3 = async (file: File): Promise<{ success: boolean; url?: string; error?: string }> => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost/s3/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Upload failed' }))
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return { success: true, url: result.url || result.location }
    } catch (error) {
      console.error('S3 upload error:', error)
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown upload error' 
      }
    }
  }

  const generateAITags = (fileName: string): { tags: string[]; subtags: { [tagId: string]: string[] } } => {
    // Simulate AI tagging based on filename
    const name = fileName.toLowerCase()
    const tags: string[] = []
    const subtags: { [tagId: string]: string[] } = {}

    if (name.includes("financial") || name.includes("finance")) {
      tags.push("Financial Report")
      subtags["Financial Report"] = ["Income Statement", "Cash Flow"]
    }
    if (name.includes("risk")) {
      tags.push("Risk Management")
      subtags["Risk Management"] = ["Credit Risk", "Market Risk"]
    }
    if (name.includes("investment")) {
      tags.push("Investment")
      subtags["Investment"] = ["Equity Investment", "Fixed Income"]
    }
    if (name.includes("market")) {
      tags.push("Market Analysis")
      subtags["Market Analysis"] = ["Technical Analysis", "Market Trends"]
    }
    if (name.includes("compliance")) {
      tags.push("Compliance")
      subtags["Compliance"] = ["Regulatory Compliance", "Internal Audit"]
    }
    if (
      name.includes("quarterly") ||
      name.includes("q1") ||
      name.includes("q2") ||
      name.includes("q3") ||
      name.includes("q4")
    ) {
      tags.push("Quarterly")
      subtags["Quarterly"] = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"].filter((q) =>
        name.includes(q.toLowerCase().replace(" ", "_")),
      )
      if (subtags["Quarterly"].length === 0) {
        subtags["Quarterly"] = ["Current Quarter"]
      }
    }
    if (name.includes("annual")) {
      tags.push("Annual")
      subtags["Annual"] = ["Annual Report", "Year-end Summary"]
    }
    if (name.includes("strategy")) {
      tags.push("Strategy")
      subtags["Strategy"] = ["Business Strategy", "Investment Strategy"]
    }
    if (name.includes("portfolio")) {
      tags.push("Portfolio")
      subtags["Portfolio"] = ["Portfolio Analysis", "Asset Allocation"]
    }

    // Add some default tags if none found
    if (tags.length === 0) {
      tags.push("Document", "Unclassified")
      subtags["Document"] = ["General Document"]
      subtags["Unclassified"] = ["Needs Review"]
    }

    return { tags, subtags }
  }

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file)
    setIsUploading(true)
    setUploadProgress(0)
    setUploadError(null)

    try {
      // Step 1: Upload to S3 (0-70% progress)
      setUploadProgress(10)
      
      const s3Result = await uploadToS3(file)
      
      if (!s3Result.success) {
        throw new Error(s3Result.error || 'Failed to upload to S3')
      }

      setUploadProgress(70)

      // Step 2: Simulate AI processing (70-100% progress)
      const processingInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) {
            clearInterval(processingInterval)
            return 95
          }
          return prev + 5
        })
      }, 200)

      // Simulate AI processing delay
      await new Promise((resolve) => setTimeout(resolve, 2000))
      clearInterval(processingInterval)
      setUploadProgress(100)

      // Step 3: Create document with AI tags
      const aiResult = generateAITags(file.name)
      const newDocument: Document = {
        id: Date.now().toString(),
        name: file.name,
        uploadDate: new Date().toISOString().split("T")[0],
        tags: aiResult.tags,
        subtags: aiResult.subtags,
        size: formatFileSize(file.size),
        status: "pending",
      }

      // Complete the upload
      setTimeout(() => {
        onUploadComplete(newDocument)
        setIsUploading(false)
        setUploadProgress(0)
        setUploadedFile(null)
      }, 500)

    } catch (error) {
      console.error('Upload failed:', error)
      setUploadError(error instanceof Error ? error.message : 'Upload failed')
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const handleClose = () => {
    if (!isUploading) {
      onClose()
      setUploadedFile(null)
      setUploadProgress(0)
      setUploadError(null)
    }
  }

  const handleRetry = () => {
    if (uploadedFile) {
      setUploadError(null)
      handleFileUpload(uploadedFile)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Upload className="w-5 h-5 text-red-600" />
            <span>Upload Document</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {!isUploading && !uploadedFile && !uploadError && (
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragOver ? "border-red-500 bg-red-50" : "border-gray-300 hover:border-red-400 hover:bg-gray-50"
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium text-gray-900 mb-2">Drop your document here</p>
              <p className="text-sm text-gray-500 mb-4">or click to browse files</p>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.txt"
                className="hidden"
                id="file-upload"
              />
              <Button variant="outline" onClick={handleBrowseClick} className="cursor-pointer">
                Browse Files
              </Button>
              <p className="text-xs text-gray-400 mt-2">Supported formats: PDF, DOC, DOCX, XLS, XLSX, TXT</p>
            </div>
          )}

          {isUploading && uploadedFile && (
            <div className="space-y-4">
              <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                <FileText className="w-8 h-8 text-red-600" />
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                  <p className="text-sm text-gray-500">{formatFileSize(uploadedFile.size)}</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">
                  {uploadProgress < 70 
                      ? "Uploading to S3..." 
                      : uploadProgress < 100 
                      ? "Processing with AI..." 
                      : "Complete!"
                    }
                  </span>
                  <span className="text-gray-900">{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2" />
              </div>

              {uploadProgress === 100 && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm font-medium">Upload complete! Processing tags...</span>
                </div>
              )}
            </div>
          )}
          {uploadError && (
            <div className="space-y-4">
              <div className="flex items-center space-x-3 p-4 bg-red-50 rounded-lg border border-red-200">
                <AlertCircle className="w-8 h-8 text-red-600" />
                <div className="flex-1">
                  <p className="font-medium text-red-900">Upload Failed</p>
                  <p className="text-sm text-red-700">{uploadError}</p>
                </div>
              </div>
              
              <div className="flex space-x-2">
                <Button 
                  variant="outline" 
                  onClick={handleRetry}
                  className="flex-1"
                >
                  Try Again
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setUploadError(null)
                    setUploadedFile(null)
                  }}
                  className="flex-1"
                >
                  Choose Different File
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            {isUploading ? "Uploading..." : "Cancel"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
