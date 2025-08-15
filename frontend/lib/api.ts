/**
 * API client for Document Service
 */

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost'
const DOCUMENT_SERVICE_URL = `${API_BASE_URL}/documents`
const CATEGORIES_SERVICE_URL = `${API_BASE_URL}/categories`

// For direct service access during development (if nginx is not being used)
const DIRECT_DOCUMENT_SERVICE_URL = process.env.NEXT_PUBLIC_DOCUMENT_SERVICE_URL || '/api'
const DIRECT_CATEGORIES_SERVICE_URL = process.env.NEXT_PUBLIC_CATEGORIES_SERVICE_URL || '/api'

// Types from backend
export interface BackendDocument {
  document_id: number
  document_name: string
  document_type: string
  link: string
  categories: number[]
  company: number
  uploaded_by: number
  upload_date: string
}

export interface BackendCategory {
  category_id: number
  category_name: string
  description: string
  parent_category_id: number | null
  created_at: string
}

export interface APIResponse<T> {
  status: 'success' | 'error'
  message: string
  data: T
  timestamp: string
  error_code?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    currentPage: number
    totalPages: number
    totalItems: number
    itemsPerPage: number
    hasNextPage: boolean
    hasPreviousPage: boolean
  }
}

// Frontend types (existing)
export interface Document {
  id: string
  name: string
  uploadDate: string
  tags: string[]
  subtags: { [tagId: string]: string[] }
  size: string
  type?: string
  link?: string
  company?: number
  uploadedBy?: number
}

export interface Category {
  id: number
  name: string
  description: string
  parentId: number | null
  children: Category[]
}

class APIClient {
  private async fetchWithErrorHandling<T>(url: string, options?: RequestInit): Promise<APIResponse<T>> {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`)
      }

      return data
    } catch (error) {
      console.error(`API Error for ${url}:`, error)
      throw error
    }
  }

  // Document Service Methods
  async getDocuments(params?: {
    limit?: number
    offset?: number
    search?: string
  }): Promise<PaginatedResponse<BackendDocument>> {
    const searchParams = new URLSearchParams()
    
    if (params?.limit) searchParams.append('limit', params.limit.toString())
    if (params?.offset) searchParams.append('offset', params.offset.toString())
    if (params?.search) searchParams.append('search', params.search)

    // First, get the requested documents
    const url = `${DIRECT_DOCUMENT_SERVICE_URL}/documents${searchParams.toString() ? `?${searchParams.toString()}` : ''}`
    const response = await this.fetchWithErrorHandling<BackendDocument[]>(url)
    
    // Get total count for pagination (we'll fetch without limit to get total)
    const totalUrl = `${DIRECT_DOCUMENT_SERVICE_URL}/documents${params?.search ? `?search=${params.search}` : ''}`
    const totalResponse = await this.fetchWithErrorHandling<BackendDocument[]>(totalUrl)
    
    const limit = params?.limit || 15
    const offset = params?.offset || 0
    const totalItems = totalResponse.data.length
    const currentPage = Math.floor(offset / limit) + 1
    const totalPages = Math.ceil(totalItems / limit)
    
    return {
      data: response.data,
      pagination: {
        currentPage,
        totalPages,
        totalItems,
        itemsPerPage: limit,
        hasNextPage: currentPage < totalPages,
        hasPreviousPage: currentPage > 1,
      }
    }
  }

  async getDocument(id: number): Promise<BackendDocument> {
    const response = await this.fetchWithErrorHandling<BackendDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`)
    return response.data
  }

  async createDocument(document: Omit<BackendDocument, 'document_id' | 'upload_date'>): Promise<BackendDocument> {
    const response = await this.fetchWithErrorHandling<BackendDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents`, {
      method: 'POST',
      body: JSON.stringify(document),
    })
    return response.data
  }

  async updateDocument(id: number, document: Partial<Omit<BackendDocument, 'document_id'>>): Promise<BackendDocument> {
    const response = await this.fetchWithErrorHandling<BackendDocument>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(document),
    })
    return response.data
  }

  async deleteDocument(id: number): Promise<void> {
    await this.fetchWithErrorHandling<null>(`${DIRECT_DOCUMENT_SERVICE_URL}/documents/${id}`, {
      method: 'DELETE',
    })
  }

  // Categories Service Methods
  async getCategories(): Promise<BackendCategory[]> {
    const response = await fetch(`${DIRECT_CATEGORIES_SERVICE_URL}/categories`)
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`)
    }

    // Categories service returns array directly, not wrapped in APIResponse
    return Array.isArray(data) ? data : data.data || []
  }

  async getCategory(id: number): Promise<BackendCategory> {
    const response = await fetch(`${DIRECT_CATEGORIES_SERVICE_URL}/categories/${id}`)
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`)
    }

    return Array.isArray(data) ? data[0] : data.data || data
  }
}

// Utility functions to transform backend data to frontend format
export function transformBackendDocument(
  backendDoc: BackendDocument, 
  categoriesMap: Map<number, BackendCategory>
): Document {
  // Map categories to tag names
  const tags = backendDoc.categories.map(catId => {
    const category = categoriesMap.get(catId)
    return category ? category.category_name : `Category ${catId}`
  })

  // Create subtags based on parent-child relationships
  const subtags: { [tagId: string]: string[] } = {}
  
  backendDoc.categories.forEach(catId => {
    const category = categoriesMap.get(catId)
    if (category) {
      // Find child categories
      const children = Array.from(categoriesMap.values())
        .filter(cat => cat.parent_category_id === catId)
        .map(cat => cat.category_name)
      
      if (children.length > 0) {
        subtags[category.category_name] = children
      }
    }
  })

  // Generate a file size (since backend doesn't have this, we'll estimate based on file type)
  const sizeEstimate = estimateFileSize(backendDoc.document_type)

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
    uploadedBy: backendDoc.uploaded_by,
  }
}

export function buildCategoriesMap(categories: BackendCategory[]): Map<number, BackendCategory> {
  const map = new Map<number, BackendCategory>()
  categories.forEach(category => {
    map.set(category.category_id, category)
  })
  return map
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

// Export types for external use
export type { APIResponse, BackendDocument, BackendCategory, Document, Category }