/**
 * Custom hook for managing document data
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, transformBackendDocument, type BackendDocument } from '@/lib/api'
import type { Document } from '@/types'

interface UseDocumentsParams {
  limit?: number
  offset?: number
  search?: string
  autoFetch?: boolean
}

interface PaginationInfo {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  hasNextPage: boolean
  hasPreviousPage: boolean
}

interface UseDocumentsReturn {
  documents: Document[]
  pagination: PaginationInfo | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  createDocument: (document: Omit<BackendDocument, 'document_id' | 'upload_date'>) => Promise<void>
  updateDocument: (id: number, document: Partial<Omit<BackendDocument, 'document_id'>>) => Promise<void>
  deleteDocument: (id: number) => Promise<void>
}

export function useDocuments(params: UseDocumentsParams = {}): UseDocumentsReturn {
  const { limit, offset, search, autoFetch = true } = params
  
  // Documents state
  const [documents, setDocuments] = useState<Document[]>([])
  const [pagination, setPagination] = useState<PaginationInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)


  // Fetch documents
  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch documents
      const documentsResponse = await apiClient.getDocuments({ limit, offset, search })
      
      // Transform backend documents to frontend format
      const documentsData = documentsResponse?.data || []
      const transformedDocuments = documentsData.map(doc => 
        transformBackendDocument(doc)
      )

      setDocuments(transformedDocuments)
      setPagination(documentsResponse?.pagination || { total: 0, page: 1, totalPages: 1 })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch documents'
      setError(errorMessage)
      console.error('Error fetching documents:', err)
      
      // Fallback to empty array on error
      setDocuments([])
      setPagination(null)
    } finally {
      setLoading(false)
    }
  }, [limit, offset, search]) // Removed categories dependency to avoid infinite loops

  // Create document
  const createDocument = useCallback(async (document: Omit<BackendDocument, 'document_id' | 'upload_date'>) => {
    try {
      await apiClient.createDocument(document)
      // Refetch documents after creation
      await fetchDocuments()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create document'
      setError(errorMessage)
      throw err
    }
  }, [fetchDocuments])

  // Update document
  const updateDocument = useCallback(async (id: number, document: Partial<Omit<BackendDocument, 'document_id'>>) => {
    try {
      await apiClient.updateDocument(id, document)
      // Refetch documents after update
      await fetchDocuments()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update document'
      setError(errorMessage)
      throw err
    }
  }, [fetchDocuments])

  // Delete document
  const deleteDocument = useCallback(async (id: number) => {
    try {
      await apiClient.deleteDocument(id)
      // Remove from local state immediately for better UX
      setDocuments(prev => prev.filter(doc => doc.id !== id.toString()))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete document'
      setError(errorMessage)
      // Refetch on error to ensure consistency
      await fetchDocuments()
      throw err
    }
  }, [fetchDocuments])

  // Auto-fetch on mount and when params change
  useEffect(() => {
    if (autoFetch) {
      fetchDocuments()
    }
  }, [fetchDocuments, autoFetch])


  return {
    documents,
    pagination,
    loading,
    error,
    refetch: fetchDocuments,
    createDocument,
    updateDocument,
    deleteDocument,
  }
}

// Hook for getting available tags and subtags from documents
export function useDocumentTags(documents: Document[]) {
  const availableTags = useState(() => {
    const tags = new Set<string>()
    documents.forEach((doc) => doc.tags.forEach((tag) => tags.add(tag)))
    return Array.from(tags).sort()
  })

  const getAvailableSubtags = useCallback((filterTag: string) => {
    if (!filterTag) return []
    const subtags = new Set<string>()
    documents.forEach((doc) => {
      if (doc.tags.includes(filterTag) && doc.subtags[filterTag]) {
        doc.subtags[filterTag].forEach((subtag) => subtags.add(subtag))
      }
    })
    return Array.from(subtags).sort()
  }, [documents])

  return {
    availableTags: availableTags[0],
    getAvailableSubtags,
  }
}