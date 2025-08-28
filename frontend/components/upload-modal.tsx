"use client"

import type React from "react"
import { useState, useCallback, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react"

export interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  subtags: { [tagId: string]: string[] }
  size: string
  status: string
  // optional for tag confirmation flow
  modelGeneratedTags?: { tag: string; score?: number; isConfirmed?: boolean }[]
  userAddedTags?: string[]
}

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUploadComplete: (document: Document) => void
}

function UploadModal({ isOpen, onClose, onUploadComplete }: UploadModalProps) {
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
      const file = files[0]
      if (file.size > 80 * 1024 * 1024) {
        setUploadError("File size exceeds 80 MB limit.")
        return
      }
      handleFileUpload(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const file = files[0]
      if (file.size > 80 * 1024 * 1024) {
        setUploadError("File size exceeds 80 MB limit.")
        return
      }
      handleFileUpload(file)
    }
  }

  const handleBrowseClick = () => fileInputRef.current?.click()

  // Upload to S3 via your Nginx backend, using Next.js rewrites
  const uploadToS3 = async (
    file: File
  ): Promise<{ success: boolean; url?: string; error?: string }> => {
    const endpoint = "/s3/upload"; // ✅ relative path (no http://...); works locally & on Vercel
    const formData = new FormData();
    formData.append("file", file);

    // Timeout guard (optional)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60_000); // 60s

    try {
      console.log(
        `📤 [UploadToS3] Starting upload: ${file.name} size: ${file.size}`
      );

      const res = await fetch(endpoint, {
        method: "POST",
        body: formData,
        // cache: "no-store" avoids any caching issues
        cache: "no-store",
        signal: controller.signal,
      });

      // HTTP-level error
      if (!res.ok) {
        let serverMsg = "Upload failed";
        try {
          const errJson = await res.json();
          serverMsg = errJson?.error || serverMsg;
        } catch {
          // If server didn't send JSON, try text for clues
          try {
            const errText = await res.text();
            if (errText) serverMsg = errText.slice(0, 300);
          } catch {}
        }
        console.error(
          `💥 [UploadToS3] HTTP ${res.status} ${res.statusText} — ${serverMsg}`
        );
        return {
          success: false,
          error: `${serverMsg} (HTTP ${res.status})`,
        };
      }

      // Success — try to parse JSON
      let data: any = null;
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        data = await res.json();
      } else {
        // if backend returns text/plain, try to parse anyway
        const text = await res.text();
        try {
          data = JSON.parse(text);
        } catch {
          console.warn(
            "⚠️ [UploadToS3] Non-JSON response from server:",
            text?.slice(0, 300)
          );
        }
      }

      const s3Url = data?.s3_url || data?.url;
      if (!s3Url) {
        console.warn("⚠️ [UploadToS3] Upload succeeded but no URL in response:", data);
      } else {
        console.log(`✅ [UploadToS3] Uploaded OK → ${s3Url}`);
      }

      return { success: true, url: s3Url };
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === "AbortError"
          ? "Upload timed out"
          : err instanceof Error
          ? err.message
          : "Unknown upload error";
      console.error("🔥 [UploadToS3] Exception caught:", err);
      return { success: false, error: message };
    } finally {
      clearTimeout(timeoutId);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (file.size > 80 * 1024 * 1024) {
      setUploadError("File size exceeds 80 MB limit.")
      return
    }

    setUploadedFile(file)
    setIsUploading(true)
    setUploadProgress(0)
    setUploadError(null)

    try {
      setUploadProgress(10)
      const s3Result = await uploadToS3(file)
      if (!s3Result.success) throw new Error(s3Result.error || "Failed to upload to S3")
      setUploadProgress(70)

      // Simulate /v1/predict
      setUploadProgress(75)
      await new Promise((r) => setTimeout(r, 1200))
      const predictJson = {
        results: [
          {
            filename: file.name,
            tags: [
              { tag: "news", score: 0.92 },
              { tag: "Recommendations", score: 0.81 },
            ],
            user_labels: ["Discovery Event", "FY2024"],
          },
        ],
      }
      const first = predictJson.results?.[0]
      if (!first) throw new Error("No prediction results returned")
      setUploadProgress(100)

      const newDocument: Document = {
        id: Date.now().toString(),
        name: file.name,
        uploadDate: new Date().toISOString().split("T")[0],
        tags: (first.tags || []).map((t: any) => t.tag),
        subtags: {
          ...(first.user_labels ? { "User Labels": first.user_labels } : {}),
          "Model Tags (w/ confidence)": first.tags.map(
            (t: any) => `${t.tag} (${Math.round(t.score * 100)}%)`
          ),
        },
        size: formatFileSize(file.size),
        status: "pending",
        modelGeneratedTags: (first.tags ?? []).map((t: any) => ({
          tag: t.tag,
          score: t.score,
          isConfirmed: true,
        })),
        userAddedTags: first.user_labels ?? [],
      }

      setTimeout(() => {
        onUploadComplete(newDocument)
        setIsUploading(false)
        setUploadProgress(0)
        setUploadedFile(null)
      }, 400)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed")
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const formatFileSize = (bytes: number) => {
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
                      : "Complete!"}
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
                <Button variant="outline" onClick={handleRetry} className="flex-1">
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

export default UploadModal
export { UploadModal }
