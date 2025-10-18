/**
 * Custom hook for managing document data (with server-side search/sort)
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  apiClient,
  transformBackendDocument,
  type BackendProcessedDocument,
  type Document
} from '@/lib/api'

interface UseDocumentsParams {
  limit?: number
  offset?: number
  search?: string
  sortBy?: 'name' | 'date' | 'size'
  sortOrder?: 'asc' | 'desc'
  status?: string
  companyId?: number
  primaryTags?: string[]
  secondaryTags?: string[]
  tertiaryTags?: string[]
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
  createDocument: (document: Omit<BackendProcessedDocument, 'process_id' | 'processing_date'>) => Promise<void>
  updateDocument: (id: number, document: Partial<Omit<BackendProcessedDocument, 'process_id'>>) => Promise<void>
  deleteDocument: (id: number) => Promise<void>
}

export function useDocuments(params: UseDocumentsParams = {}): UseDocumentsReturn {
  const {
    limit,
    offset,
    search,
    sortBy,
    sortOrder,
    status,
    companyId,
    primaryTags,
    secondaryTags,
    tertiaryTags,
    autoFetch = true
  } = params
  
  const [documents, setDocuments] = useState<Document[]>([])
  const [pagination, setPagination] = useState<PaginationInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    setError(null)
    console.log('[useDocuments] fetchDocuments -> params', {
      limit, offset, search, sortBy, sortOrder, status, companyId, primaryTags, secondaryTags, tertiaryTags
    })

    try {
      // NOTE: apiClient.getDocuments returns { documents, pagination }
      const { documents: backendDocs, pagination: apiPagination } =
        await apiClient.getDocuments({
          limit,
          offset,
          search,
          sortBy,
          sortOrder,
          status,
          companyId,
          primaryTags,
          secondaryTags,
          tertiaryTags,
        })

      const transformed = (backendDocs || []).map(transformBackendDocument)
      setDocuments(transformed)

      if (apiPagination) {
        const info: PaginationInfo = {
          currentPage: apiPagination.page,
          totalPages: apiPagination.totalPages,
          totalItems: apiPagination.total,
          itemsPerPage: apiPagination.limit ?? (limit || 15),
          hasNextPage: apiPagination.page < apiPagination.totalPages,
          hasPreviousPage: apiPagination.page > 1,
        }
        setPagination(info)
      } else {
        // Fallback (shouldn't happen)
        setPagination({
          currentPage: 1,
          totalPages: 1,
          totalItems: transformed.length,
          itemsPerPage: limit || 15,
          hasNextPage: false,
          hasPreviousPage: false,
        })
      }

      console.log('[useDocuments] fetchDocuments -> success', {
        returned: transformed.length,
        pagination: apiPagination
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch documents'
      setError(message)
      console.error('[useDocuments] fetchDocuments -> error', err)
      setDocuments([])
      setPagination(null)
    } finally {
      setLoading(false)
    }
  }, [limit, offset, search, sortBy, sortOrder, status, companyId, primaryTags, secondaryTags, tertiaryTags])

  // CRUD helpers
  const createDocument = useCallback(async (
    document: Omit<BackendProcessedDocument, 'process_id' | 'processing_date'>
  ) => {
    try {
      await apiClient.createDocument(document)
      await fetchDocuments()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create document'
      setError(message)
      throw err
    }
  }, [fetchDocuments])

  const updateDocument = useCallback(async (
    id: number,
    document: Partial<Omit<BackendProcessedDocument, 'process_id'>>
  ) => {
    try {
      await apiClient.updateDocument(id, document)
      await fetchDocuments()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update document'
      setError(message)
      throw err
    }
  }, [fetchDocuments])

  const deleteDocument = useCallback(async (id: number) => {
    try {
      await apiClient.deleteDocument(id)
      // Optimistic local update
      setDocuments(prev => prev.filter(doc => doc.id !== id.toString()))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete document'
      setError(message)
      await fetchDocuments()
      throw err
    }
  }, [fetchDocuments])

  // Auto-fetch on mount/param changes
  useEffect(() => {
    if (autoFetch) fetchDocuments()
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

// Hook for getting available tags from documents (memoized)
export function useDocumentTags(documents: Document[]) {
  const availableTags = useMemo(() => {
    const tags = new Set<string>()
    documents.forEach((doc) => doc.tags.forEach((tag) => tags.add(tag)))
    return Array.from(tags).sort()
  }, [documents])

  return { availableTags }
}
