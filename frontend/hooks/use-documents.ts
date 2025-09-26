/**
 * Custom hook for managing document data
 */

import { useState, useEffect, useCallback } from 'react'
import { apiClient, transformBackendDocument, type BackendProcessedDocument, type Document } from '@/lib/api'

type SortBy = 'name' | 'date' | 'size'
type SortOrder = 'asc' | 'desc'

interface UseDocumentsParams {
  limit?: number
  offset?: number
  search?: string
  sort_by?: SortBy      // NEW
  sort_order?: SortOrder // NEW
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
  const { limit, offset, search, sort_by, sort_order, autoFetch = true } = params
  
  const [documents, setDocuments] = useState<Document[]>([])
  const [pagination, setPagination] = useState<PaginationInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Forward sort params to API (backend expects sort_by & sort_order)
      const documentsResponse = await apiClient.getDocuments({
        limit,
        offset,
        search,
        sort_by,
        sort_order,
      })

      // NOTE: assuming your apiClient already unwraps the APIResponse and returns:
      // { data: BackendProcessedDocument[], pagination: { total, page, totalPages, ... } }
      // If it returns the raw envelope, adjust to: documentsResponse.data.documents, documentsResponse.data.pagination
      const documentsData = documentsResponse?.data || []
      const transformed = documentsData.map((doc) => transformBackendDocument(doc))
      setDocuments(transformed)

      const apiPagination = documentsResponse?.pagination
      if (apiPagination) {
        const paginationInfo: PaginationInfo = {
          currentPage: apiPagination.page,
          totalPages: apiPagination.totalPages,
          totalItems: apiPagination.total,
          itemsPerPage: limit || 15,
          hasNextPage: apiPagination.page < apiPagination.totalPages,
          hasPreviousPage: apiPagination.page > 1,
        }
        setPagination(paginationInfo)
      } else {
        setPagination({
          currentPage: 1,
          totalPages: 1,
          totalItems: transformed.length,
          itemsPerPage: limit || 15,
          hasNextPage: false,
          hasPreviousPage: false,
        })
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch documents'
      setError(msg)
      console.error('Error fetching documents:', err)
      setDocuments([])
      setPagination(null)
    } finally {
      setLoading(false)
    }
  }, [limit, offset, search, sort_by, sort_order]) // ← include sort deps

  const createDocument = useCallback(async (document: Omit<BackendProcessedDocument, 'process_id' | 'processing_date'>) => {
    try {
      await apiClient.createDocument(document)
      await fetchDocuments()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to create document'
      setError(msg)
      throw err
    }
  }, [fetchDocuments])

  const updateDocument = useCallback(async (id: number, document: Partial<Omit<BackendProcessedDocument, 'process_id'>>) => {
    try {
      await apiClient.updateDocument(id, document)
      await fetchDocuments()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update document'
      setError(msg)
      throw err
    }
  }, [fetchDocuments])

  const deleteDocument = useCallback(async (id: number) => {
    try {
      await apiClient.deleteDocument(id)
      setDocuments((prev) => prev.filter((doc) => doc.id !== id.toString()))
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete document'
      setError(msg)
      await fetchDocuments()
      throw err
    }
  }, [fetchDocuments])

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

// Tags helper — small improvement: useMemo instead of useState
import { useMemo } from 'react'
export function useDocumentTags(documents: Document[]) {
  const availableTags = useMemo(() => {
    const tags = new Set<string>()
    documents.forEach((doc) => doc.tags.forEach((tag) => tags.add(tag)))
    return Array.from(tags).sort()
  }, [documents])

  return { availableTags }
}
