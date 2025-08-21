// api.ts - Frontend API client for document management
import type { DocumentPaginationResponse, Document } from '../types'

// Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost'
const DOCUMENT_SERVICE_URL = `${API_BASE_URL}/documents`

// For direct service access during development (if nginx is not being used)
const DIRECT_DOCUMENT_SERVICE_URL = process.env.NEXT_PUBLIC_DOCUMENT_SERVICE_URL || 'http://localhost:5003'

// Types from backend
export interface BackendDocument {
  document_id: number
  document_name: string
  document_type: string
  link: string
  company: number
  uploaded_by: number
  upload_date: string
  file_size?: number
  file_hash?: string
  status?: string
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
    data: BackendDocument[]
    pagination: { total: number; page: number; totalPages: number }
  }> {
    const params = new URLSearchParams()
    if (options.limit) params.append('limit', options.limit.toString())
    if (options.offset) params.append('offset', options.offset.toString())
    if (options.search) params.append('search', options.search)

    const url = `${DIRECT_DOCUMENT_SERVICE_URL}/documents${params.toString() ? `?${params}` : ''}`
    console.log('Calling document service at:', url)
    
    // Backend returns documents array directly in the data field
    const documentsArray = await this.fetchWithErrorHandling<BackendDocument[]>(url)
    
    // Create pagination info (backend doesn't provide this yet, so we'll estimate)
    const pagination = {
      total: documentsArray.length,
      page: Math.floor((options.offset || 0) / (options.limit || 15)) + 1,
      totalPages: Math.ceil(documentsArray.length / (options.limit || 15))
    }

    return {
      data: documentsArray,
      pagination
    }
  }

  async getDocument(id: number): Promise<BackendDocument> {
    return await this.fetchWithErrorHandling<BackendDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`)
  }

  async createDocument(document: Omit<BackendDocument, 'document_id' | 'upload_date'>): Promise<BackendDocument> {
    return await this.fetchWithErrorHandling<BackendDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents`, {
      method: 'POST',
      body: JSON.stringify(document),
    })
  }

  async updateDocument(id: number, document: Partial<Omit<BackendDocument, 'document_id'>>): Promise<BackendDocument> {
    return await this.fetchWithErrorHandling<BackendDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(document),
    })
  }

  async deleteDocument(id: number): Promise<void> {
    await this.fetchWithErrorHandling<null>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`, {
      method: 'DELETE',
    })
  }
}

// Utility functions to transform backend data to frontend format
export function transformBackendDocument(
  backendDoc: BackendDocument
): Document {
  // In the new schema, documents don't have categories field anymore
  // For now, return empty tags until we implement tag extraction from processed_documents
  const tags: string[] = []
  const subtags: { [tagId: string]: string[] } = {}

  // Use actual file size from backend if available, otherwise estimate
  const sizeEstimate = backendDoc.file_size 
    ? formatFileSize(backendDoc.file_size) 
    : estimateFileSize(backendDoc.document_type)

  return {
    id: backendDoc.document_id.toString(),
    name: backendDoc.document_name,
    uploadDate: backendDoc.upload_date.split('T')[0], // Extract date part
    tags: tags,
    subtags: subtags,
    size: sizeEstimate,
    type: backendDoc.document_type,
    link: backendDoc.link,
    company: backendDoc.company,
    uploaded_by: backendDoc.uploaded_by,
    status: backendDoc.status || 'uploaded'
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