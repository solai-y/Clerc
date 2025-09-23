"use client"

import type React from "react"
import { useState, useCallback, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api"
import { EnhancedConfirmTagsModal } from "./enhanced-confirm-tags-modal"

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
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [pendingDocument, setPendingDocument] = useState<Document | null>(null)
  const [predictionData, setPredictionData] = useState<any>(null)
  const [explanationData, setExplanationData] = useState<any[]>([])
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

  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }

  const uploadToS3 = async (file: File): Promise<{ success: boolean; url?: string; error?: string }> => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/s3/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Upload failed' }))
        console.error("❌ PDF upload failed with status:", response.status, errorData)
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      console.log("✅ PDF upload successful")
      console.log("📦 S3 Upload API JSON response:", result)

      // Extract s3_url from response
      return { success: true, url: result.s3_url }
    } catch (error) {
      console.error('S3 upload error:', error)
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown upload error' 
      }
      handleFileUpload(file)
    }
  }

  type PredictTag = { tag: string; score: number }
  type PredictResult = {
    filename: string
    tags?: PredictTag[]
    probs?: PredictTag[]      // tolerate alternate keys
    top5?: PredictTag[]       // "
    user_labels?: string[]
    ocr_used: boolean
    processing_ms: number
  }
  type PredictResponse = {
    threshold_pct?: number
    results: PredictResult[]
    errors?: string[]
    request_id?: string
  }

  async function predictTags(text: string, confidenceThresholds = { primary: 0.90, secondary: 0.85, tertiary: 0.80 }) {
    const requestData = {
      text: text,
      predict_levels: ["primary", "secondary", "tertiary"],
      confidence_thresholds: confidenceThresholds
    };

    const res = await fetch("/predict/classify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestData)
    });

    let json: any;
    try {
      json = await res.json();
    } catch {
      throw new Error(`Prediction service: invalid JSON (status ${res.status})`);
    }

    console.log("🔍 prediction service JSON:", json);

    if (!res.ok) {
      const msg = json?.detail || json?.error || JSON.stringify(json);
      throw new Error(`Prediction service ${res.status}: ${msg}`);
    }

    return json;
  }

  // Extract text from file for prediction service
  async function extractTextFromFile(file: File): Promise<string> {
    // For now, return filename as text placeholder
    // In production, you'd use a text extraction service
    return `Document: ${file.name}. This is a placeholder text extraction for document classification. The document appears to be a ${file.type || 'PDF'} file with a size of ${Math.round(file.size / 1024)} KB. This sample text provides sufficient content for the machine learning models to process and classify the document into appropriate categories.`;
  }
  
  



  const handleFileUpload = async (file: File) => {
    const maxSize = 80 * 1024 * 1024 // 80 MB in bytes
    if (file.size > maxSize) {
      setUploadError("File size exceeds 80 MB limit.")
      return
    }
    
    setUploadedFile(file)
    setIsUploading(true)
    setUploadProgress(0)
    setUploadError(null)

    try {
      // Step 1: Upload to S3 (0-30% progress)
      setUploadProgress(10)
      
      const s3Result = await uploadToS3(file)
      
      if (!s3Result.success) {
        throw new Error(s3Result.error || 'Failed to upload to S3')
      }
      
      const s3Link = s3Result.url
      console.log("🌐 Stored S3 Link:", s3Link)
      setUploadProgress(30)

      // Step 2: Create raw_documents entry in Supabase (30-50% progress)
      console.log("📝 Creating raw document entry in database...")
      const rawDocumentData = {
        document_name: file.name,
        document_type: file.type.toUpperCase() || "PDF",
        link: s3Link || "",
        file_size: file.size,
        status: "uploaded"
      }
      
      const rawDocResponse = await apiClient.createRawDocument(rawDocumentData)
      const documentId = rawDocResponse.document_id
      console.log("✅ Created raw document with ID:", documentId)
      setUploadProgress(50)

      // Step 3: Extract text and run prediction service processing (50-80% progress)
      setUploadProgress(60)
      console.log("🤖 Processing with Prediction Service...")
      
      // Extract text from file
      const documentText = await extractTextFromFile(file)
      
      // Get current confidence thresholds from localStorage or use defaults
      let thresholds = { primary: 0.90, secondary: 0.85, tertiary: 0.80 };
      try {
        const saved = localStorage.getItem('confidence_thresholds');
        if (saved) {
          const savedThresholds = JSON.parse(saved);
          thresholds = { ...thresholds, ...savedThresholds };
        }
      } catch (error) {
        console.warn('Failed to load saved thresholds:', error);
      }

      console.log("📊 Using confidence thresholds:", thresholds);

      // Call prediction service with confidence thresholds
      const predictionResponse = await predictTags(documentText, thresholds)
      console.log("🤖 Prediction service response:", predictionResponse)
      console.log("🔍 Service calls:", predictionResponse.service_calls)
      console.log("📊 Confidence analysis:", predictionResponse.confidence_analysis)

      // Debug: Log each level prediction in detail
      if (predictionResponse.prediction) {
        for (const level of ['primary', 'secondary', 'tertiary']) {
          const levelPred = predictionResponse.prediction[level]
          console.log(`🔍 ${level} prediction:`, levelPred)
          if (levelPred) {
            console.log(`  - pred: ${levelPred.pred}`)
            console.log(`  - confidence: ${levelPred.confidence}`)
            console.log(`  - source: ${levelPred.source}`)
            console.log(`  - ai_prediction:`, levelPred.ai_prediction)
            console.log(`  - llm_prediction:`, levelPred.llm_prediction)
          }
        }
      }

      // Extract tags from prediction response with enhanced metadata
      const extractedTags: any[] = []
      const explanations: any[] = []
      const processedTags = new Set<string>() // Prevent duplicates for UI

      // Process prediction results for each level
      if (predictionResponse.prediction) {
        for (const level of ['primary', 'secondary', 'tertiary']) {
          const levelPred = predictionResponse.prediction[level]
          if (levelPred && levelPred.pred) {
            // Always add to extractedTags with hierarchy and source metadata
            extractedTags.push({
              tag: levelPred.pred,
              score: levelPred.confidence,
              hierarchy_level: level,
              source: levelPred.source || 'ai',
              is_primary: level === 'primary',
              is_secondary: level === 'secondary',
              is_tertiary: level === 'tertiary'
            })

            // Always store explanation data for each level - this ensures we capture both AI and LLM predictions
            const explanation = {
              level: level,
              tag: levelPred.pred,
              confidence: levelPred.confidence,
              reasoning: levelPred.reasoning || `${levelPred.source?.toUpperCase() || 'AI'} prediction for ${level} level`,
              source: levelPred.source || 'ai',
              shap_data: levelPred.ai_prediction?.key_evidence || null
            }
            console.log(`📋 Adding explanation for ${level}:`, explanation)
            explanations.push(explanation)

            // Also store AI prediction separately if this is an LLM override and we have AI data
            if (levelPred.source === 'llm' && levelPred.ai_prediction && levelPred.ai_prediction.pred) {
              const aiExplanation = {
                level: level,
                tag: levelPred.ai_prediction.pred,
                confidence: levelPred.ai_prediction.confidence,
                reasoning: `AI model prediction (overridden by LLM)`,
                source: 'ai',
                shap_data: levelPred.ai_prediction.key_evidence || null
              }
              console.log(`📋 Adding AI explanation for ${level}:`, aiExplanation)
              explanations.push(aiExplanation)
            }
          }
        }
      }

      if (extractedTags.length === 0) {
        throw new Error("No prediction results returned from prediction service")
      }

      setUploadProgress(80)

      // Step 4: Create processed_documents entry in Supabase (80-90% progress)
      console.log("📊 Creating processed document entry...")
      const processedDocumentData = {
        document_id: documentId,
        suggested_tags: extractedTags,
        threshold_pct: 80, // Based on our confidence thresholds
        ocr_used: false, // Text extraction method would determine this
        processing_ms: predictionResponse.elapsed_seconds ? Math.round(predictionResponse.elapsed_seconds * 1000) : null,
        explanations: explanations, // Include explanations for storage
        prediction_response: predictionResponse // Include full response for debugging
      }
      
      const processedDocResponse = await apiClient.createProcessedDocument(processedDocumentData)
      console.log("✅ Created processed document entry:", processedDocResponse)
      setUploadProgress(90)

      // Step 5: Create frontend document object with real database data
      const newDocument: Document = {
        id: documentId.toString(),
        name: file.name,
        uploadDate: new Date().toISOString().split("T")[0],
        tags: extractedTags.map((t: any) => t.tag),
        subtags: {
          "Model Tags (w/ confidence)": extractedTags.map(
            (t: any) => `${t.tag} (${Math.round((t.score ?? 0) * 100)}%)`
          ),
          "Explanations": explanations.map(
            (e: any) => `${e.level}: ${e.reasoning?.substring(0, 100)}...`
          ),
        },
        size: formatFileSize(file.size),
        status: "Success",
        modelGeneratedTags: extractedTags.map((t: any) => ({
          tag: t.tag,
          score: t.score,
          isConfirmed: false,
          hierarchy_level: t.hierarchy_level,
          source: t.source,
          is_primary: t.is_primary,
          is_secondary: t.is_secondary,
          is_tertiary: t.is_tertiary
        })),
        userAddedTags: []
      };
      
      setUploadProgress(100)

      // Store data for confirmation modal
      setPendingDocument(newDocument)
      setPredictionData(predictionResponse)
      setExplanationData(explanations)
      
      // Complete upload processing and show confirmation modal
      setTimeout(() => {
        setIsUploading(false)
        setUploadProgress(0)
        setShowConfirmModal(true)
      }, 500)

    } catch (error) {
      console.error('Upload failed:', error)
      setUploadError(error instanceof Error ? error.message : 'Upload failed')
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

  const handleConfirmTags = async (documentId: string, confirmedTags: string[], userAddedTags: string[]) => {
    if (pendingDocument) {
      // Update the document with confirmed tags
      const finalDocument: Document = {
        ...pendingDocument,
        tags: [...confirmedTags, ...userAddedTags],
        modelGeneratedTags: pendingDocument.modelGeneratedTags?.map(tag => ({
          ...tag,
          isConfirmed: confirmedTags.includes(tag.tag)
        })),
        userAddedTags: userAddedTags
      }
      
      // Update the backend with confirmed tags and explanations
      try {
        await apiClient.updateDocumentTags(parseInt(documentId), {
          confirmed_tags: confirmedTags,
          user_added_labels: userAddedTags,
          explanations: explanationData
        })
      } catch (error) {
        console.error('Failed to update tags in backend:', error)
        // Still proceed with frontend update
      }
      
      onUploadComplete(finalDocument)
      setShowConfirmModal(false)
      setPendingDocument(null)
      setPredictionData(null)
      setExplanationData([])
      setUploadedFile(null)
    }
  }

  const handleCloseConfirmModal = () => {
    setShowConfirmModal(false)
    // Reset upload modal state
    setPendingDocument(null)
    setPredictionData(null)
    setExplanationData([])
    setUploadedFile(null)
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
    <>
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
                  {uploadProgress < 30 
                      ? "Uploading to S3..." 
                      : uploadProgress < 50
                      ? "Creating document record..."
                      : uploadProgress < 80 
                      ? "Processing with AI..." 
                      : uploadProgress < 100
                      ? "Saving AI results..."
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

    {/* Enhanced Tag Confirmation Modal */}
    {showConfirmModal && pendingDocument && (
      <EnhancedConfirmTagsModal
        document={pendingDocument}
        predictions={predictionData}
        explanations={explanationData}
        onConfirm={handleConfirmTags}
        onClose={handleCloseConfirmModal}
      />
    )}
    </>
  )
}

export default UploadModal
export { UploadModal }
