"use client"

import type React from "react"

import { useState, useCallback } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, CheckCircle } from "lucide-react"
import { Document } from "@/lib/api"

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

  const generateAITags = (fileName: string): { tags: string[] } => {
    // Simulate AI tagging based on filename
    const name = fileName.toLowerCase()
    const tags: string[] = []

    if (name.includes("financial") || name.includes("finance")) {
      tags.push("Financial Report")
    }
    if (name.includes("risk")) {
      tags.push("Risk Management")
    }
    if (name.includes("investment")) {
      tags.push("Investment")
    }
    if (name.includes("market")) {
      tags.push("Market Analysis")
    }
    if (name.includes("compliance")) {
      tags.push("Compliance")
    }
    if (
      name.includes("quarterly") ||
      name.includes("q1") ||
      name.includes("q2") ||
      name.includes("q3") ||
      name.includes("q4")
    ) {
      tags.push("Quarterly")
    }
    if (name.includes("annual")) {
      tags.push("Annual")
    }
    if (name.includes("strategy")) {
      tags.push("Strategy")
    }
    if (name.includes("portfolio")) {
      tags.push("Portfolio")
    }

    // Add some default tags if none found
    if (tags.length === 0) {
      tags.push("Document", "Unclassified")
    }

    return { tags }
  }

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file)
    setIsUploading(true)
    setUploadProgress(0)

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          // Simulate AI processing and create document
          setTimeout(() => {
            const aiResult = generateAITags(file.name)
            const newDocument: Document = {
              id: Date.now().toString(),
              name: file.name,
              uploadDate: new Date().toISOString().split("T")[0],
              tags: aiResult.tags,
              size: formatFileSize(file.size),
              type: file.type || 'application/pdf',
              link: '',
              company: null,
              companyName: null,
              uploaded_by: null,
              status: 'uploaded',
              modelGeneratedTags: aiResult.tags.map(tag => ({
                tag,
                score: Math.random() * 0.5 + 0.5, // Random confidence between 0.5-1.0
                isConfirmed: false
              })),
              userAddedTags: []
            }
            onUploadComplete(newDocument)
            setIsUploading(false)
            setUploadProgress(0)
            setUploadedFile(null)
          }, 1000)
          return 100
        }
        return prev + 10
      })
    }, 200)
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
          {!isUploading && !uploadedFile && (
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
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.txt"
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload">
                <Button variant="outline" className="cursor-pointer bg-transparent">
                  Browse Files
                </Button>
              </label>
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
                    {uploadProgress < 100 ? "Uploading..." : "Processing with AI..."}
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
