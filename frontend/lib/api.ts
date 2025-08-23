// api.ts - Frontend API client for document management

// Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost'
const DOCUMENT_SERVICE_URL = `${API_BASE_URL}/documents`

// For direct service access during development (if nginx is not being used)
const DIRECT_DOCUMENT_SERVICE_URL = process.env.NEXT_PUBLIC_DOCUMENT_SERVICE_URL || 'http://localhost:5002'

// Types from backend - actual processed documents structure
export interface BackendProcessedDocument {
  process_id: number
  document_id: number
  model_id: number | null
  threshold_pct: number
  confirmed_tags: string[] | null // confirmed tags by user
  suggested_tags: Array<{
    tag: string
    score: number
  }> | null // AI suggested tags with scores
  user_added_labels: string[] | null // user manually added labels
  ocr_used: boolean
  processing_ms: number | null
  processing_date: string
  errors: string[] | null
  saved_training: boolean
  saved_count: number
  request_id: string | null
  status: string
  user_reviewed: boolean | null
  raw_documents: {
    document_name: string
    document_type: string
    link: string
    uploaded_by: number | null
    company: number | null
    upload_date: string
    file_size: number | null
    file_hash: string | null
    status: string
    companies: {
      company_id: number
      company_name: string
    } | null
  }
}

export interface APIResponse<T> {
  status: string
  message: string
  data: T
  timestamp: string
  pagination?: {
    total: number
    page: number
    totalPages: number
  }
}

export interface GetDocumentsOptions {
  limit?: number
  offset?: number
  search?: string
}

class APIClient {
  private async fetchWithErrorHandling<T>(url: string, options: RequestInit = {}): Promise<T> {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data: APIResponse<T> = await response.json()

      if (data.status !== 'success') {
        throw new Error(data.message || 'API request failed')
      }

      return data.data
    } catch (error) {
      console.error(`API Error for ${url}:`, error)
      throw error
    }
  }

  // Document Service Methods
  async getDocuments(options: GetDocumentsOptions = {}): Promise<{
    data: BackendProcessedDocument[]
    pagination: { total: number; page: number; totalPages: number }
  }> {
    const params = new URLSearchParams()
    if (options.limit) params.append('limit', options.limit.toString())
    if (options.offset) params.append('offset', options.offset.toString())
    if (options.search) params.append('search', options.search)

    const url = `${DIRECT_DOCUMENT_SERVICE_URL}/documents${params.toString() ? `?${params}` : ''}`
    console.log('Calling document service at:', url)
    
    // Backend now returns an object with processed documents and pagination info
    const responseData = await this.fetchWithErrorHandling<{
      documents: BackendProcessedDocument[]
      pagination: {
        total: number
        page: number
        totalPages: number
        limit: number
        offset: number
      }
    }>(url)
    
    const documentsArray = responseData.documents
    const pagination = responseData.pagination

    return {
      data: documentsArray,
      pagination
    }
  }

  async getDocument(id: number): Promise<BackendProcessedDocument> {
    return await this.fetchWithErrorHandling<BackendProcessedDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`)
  }

  async createDocument(document: Omit<BackendProcessedDocument, 'process_id' | 'processing_date'>): Promise<BackendProcessedDocument> {
    return await this.fetchWithErrorHandling<BackendProcessedDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents`, {
      method: 'POST',
      body: JSON.stringify(document),
    })
  }

  async updateDocument(id: number, document: Partial<Omit<BackendProcessedDocument, 'process_id'>>): Promise<BackendProcessedDocument> {
    return await this.fetchWithErrorHandling<BackendProcessedDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(document),
    })
  }

  async deleteDocument(id: number): Promise<void> {
    await this.fetchWithErrorHandling<null>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`, {
      method: 'DELETE',
    })
  }

  async updateDocumentTags(documentId: number, tagData: {
    confirmed_tags?: string[]
    user_added_labels?: string[]
    user_removed_tags?: string[]
  }): Promise<BackendProcessedDocument> {
    return await this.fetchWithErrorHandling<BackendProcessedDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${documentId}/tags`, {
      method: 'PATCH',
      body: JSON.stringify(tagData),
    })
  }
}

// Frontend Document interface
export interface Document {
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
  // Detailed tag information for modal display
  modelGeneratedTags: Array<{
    tag: string
    score: number
    isConfirmed: boolean
  }>
  userAddedTags: string[]
}

// Utility functions to transform backend data to frontend format
export function transformBackendDocument(
  processedDoc: BackendProcessedDocument
): Document {
  // Extract tags from processed document
  const tags: string[] = []
  const modelGeneratedTags: Array<{tag: string, score: number, isConfirmed: boolean}> = []
  const userAddedTags: string[] = []
  
  // Process MODEL GENERATED TAGS (from suggested_tags with scores)
  if (processedDoc.suggested_tags) {
    processedDoc.suggested_tags.forEach(tagData => {
      const isConfirmed = processedDoc.confirmed_tags?.includes(tagData.tag) || false
      modelGeneratedTags.push({
        tag: tagData.tag,
        score: tagData.score,
        isConfirmed: isConfirmed
      })
      
      // Add confirmed model tags to main tags array
      if (isConfirmed && !tags.includes(tagData.tag)) {
        tags.push(tagData.tag)
      }
    })
  }
  
  // Process USER_ADDED_LABELS (manually added by user)
  if (processedDoc.user_added_labels) {
    processedDoc.user_added_labels.forEach(userLabel => {
      userAddedTags.push(userLabel)
      if (!tags.includes(userLabel)) {
        tags.push(userLabel)
      }
    })
  }
  
  // Add any confirmed tags that weren't in suggested_tags (edge case)
  if (processedDoc.confirmed_tags) {
    processedDoc.confirmed_tags.forEach(confirmedTag => {
      if (!tags.includes(confirmedTag)) {
        tags.push(confirmedTag)
      }
    })
  }

  // Use actual file size from raw document if available, otherwise estimate
  const sizeEstimate = processedDoc.raw_documents?.file_size 
    ? formatFileSize(processedDoc.raw_documents.file_size) 
    : estimateFileSize(processedDoc.raw_documents?.document_type || 'PDF')

  return {
    id: processedDoc.document_id.toString(),
    name: processedDoc.raw_documents?.document_name || 'Unknown Document',
    uploadDate: processedDoc.raw_documents?.upload_date.split('T')[0] || '', // Extract date part
    tags: tags,
    size: sizeEstimate,
    type: processedDoc.raw_documents?.document_type || 'PDF',
    link: processedDoc.raw_documents?.link || '',
    company: processedDoc.raw_documents?.company,
    companyName: processedDoc.raw_documents?.companies?.company_name || null,
    uploaded_by: processedDoc.raw_documents?.uploaded_by,
    status: processedDoc.status || 'processed',
    modelGeneratedTags: modelGeneratedTags,
    userAddedTags: userAddedTags
  }
}


function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function estimateFileSize(documentType: string): string {
  // Simple file size estimation based on document type
  const estimates: { [key: string]: string } = {
    'PDF': `${(Math.random() * 4 + 1).toFixed(1)} MB`,
    'DOCX': `${(Math.random() * 2 + 0.5).toFixed(1)} MB`,
    'XLSX': `${(Math.random() * 5 + 2).toFixed(1)} MB`,
    'DOC': `${(Math.random() * 2 + 0.5).toFixed(1)} MB`,
    'XLS': `${(Math.random() * 5 + 2).toFixed(1)} MB`,
    'TXT': `${(Math.random() * 0.5 + 0.1).toFixed(1)} MB`,
  }
  
  return estimates[documentType.toUpperCase()] || `${(Math.random() * 3 + 1).toFixed(1)} MB`
}

// Export singleton instance
export const apiClient = new APIClient()