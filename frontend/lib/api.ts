// api.ts - Frontend API client for document management

// ---------- Build URLs correctly ----------
const isServer = typeof window === "undefined";
// On the server (SSR), talk to the real backend origin.
// On the client (browser), ALWAYS use relative paths so Next.js rewrites proxy it.
const SERVER_BACKEND_ORIGIN =
  process.env.BACKEND_ORIGIN || "http://localhost";

function apiUrl(path: string) {
  return isServer ? `${SERVER_BACKEND_ORIGIN}${path}` : path;
}

// ---------- Types from backend ----------
export interface BackendProcessedDocument {
  process_id: number;
  document_id: number;
  model_id: number | null;
  threshold_pct: number;
  confirmed_tags: string[] | null;
  suggested_tags: Array<{ tag: string; score: number }> | null;
  user_added_labels: string[] | null;
  ocr_used: boolean;
  processing_ms: number | null;
  processing_date: string;
  errors: string[] | null;
  saved_training: boolean;
  saved_count: number;
  request_id: string | null;
  status: string;
  user_reviewed: boolean | null;
  company: number | null; // Company is now in processed_documents
  raw_documents: {
    document_name: string;
    document_type: string;
    link: string;
    uploaded_by: number | null;
    upload_date: string;
    file_size: number | null;
    file_hash: string | null;
    status: string;
    companies: { company_id: number; company_name: string } | null;
  };
}

export interface APIResponse<T> {
  status: string;
  message: string;
  data: T;
  timestamp: string;
  pagination?: { total: number; page: number; totalPages: number };
}

export interface GetDocumentsOptions {
  limit?: number;
  offset?: number;
  search?: string;
  sort_by?: "name" | "date" | "size";
  sort_order?: "asc" | "desc";
}

class APIClient {
  private async fetchWithErrorHandling<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const res = await fetch(url, {
        // Only set JSON header if we actually send JSON
        headers:
          options.body && !(options.body instanceof FormData)
            ? { "Content-Type": "application/json", ...(options.headers || {}) }
            : options.headers,
        cache: "no-store",
        ...options,
      });

      if (!res.ok) {
        const msg = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${res.statusText} ${msg.slice(0, 200)}`);
      }

      const data: APIResponse<T> = await res.json();
      if (data.status !== "success") {
        throw new Error(data.message || "API request failed");
      }
      return data.data;
    } catch (error) {
      // Avoid leaking server origin in client logs
      const displayUrl = isServer ? url : new URL(url, location.origin).pathname;
      console.error(`API Error for ${displayUrl}:`, error);
      throw error;
    }
  }

  // -------- Document Service Methods (all use relative paths on client) --------
  async getDocuments(options: GetDocumentsOptions = {}): Promise<{
    data: BackendProcessedDocument[];
    pagination: { total: number; page: number; totalPages: number };
  }> {
    const params = new URLSearchParams();
    if (options.limit) params.append("limit", String(options.limit));
    if (options.offset) params.append("offset", String(options.offset));
    if (options.search) params.append("search", options.search);
    if (options.sort_by)     params.append("sort_by", options.sort_by);
    if (options.sort_order)  params.append("sort_order", options.sort_order);


    const url = apiUrl(`/documents${params.toString() ? `?${params}` : ""}`);
    if (isServer) console.log("[api] GET", url);

    const responseData = await this.fetchWithErrorHandling<{
      documents: BackendProcessedDocument[];
      pagination: { total: number; page: number; totalPages: number; limit: number; offset: number };
    }>(url);

    return { data: responseData.documents, pagination: responseData.pagination };
    }

  async getDocument(id: number): Promise<BackendProcessedDocument> {
    return this.fetchWithErrorHandling<BackendProcessedDocument>(apiUrl(`/documents/${id}`));
  }

  async createDocument(
    document: Omit<BackendProcessedDocument, "process_id" | "processing_date">
  ): Promise<BackendProcessedDocument> {
    return this.fetchWithErrorHandling<BackendProcessedDocument>(apiUrl("/documents"), {
      method: "POST",
      body: JSON.stringify(document),
    });
  }

  async updateDocument(
    id: number,
    document: Partial<Omit<BackendProcessedDocument, "process_id">>
  ): Promise<BackendProcessedDocument> {
    return this.fetchWithErrorHandling<BackendProcessedDocument>(apiUrl(`/documents/${id}`), {
      method: "PUT",
      body: JSON.stringify(document),
    });
  }

  async deleteDocument(id: number): Promise<void> {
    await this.fetchWithErrorHandling<null>(apiUrl(`/documents/${id}`), { method: "DELETE" });
  }

  async updateDocumentTags(
    documentId: number,
    tagData: {
      confirmed_tags?: string[];
      user_added_labels?: string[];
      user_removed_tags?: string[];
    }
  ): Promise<BackendProcessedDocument> {
    return this.fetchWithErrorHandling<BackendProcessedDocument>(
      apiUrl(`/documents/${documentId}/tags`),
      { method: "PATCH", body: JSON.stringify(tagData) }
    );
  }

  async getUnprocessedDocuments(limit: number = 1): Promise<{
    unprocessed_documents: any[];
    count: number;
  }> {
    return this.fetchWithErrorHandling<{ unprocessed_documents: any[]; count: number }>(
      apiUrl(`/documents/unprocessed?limit=${limit}`)
    );
  }

  async createRawDocument(data: {
    document_name: string;
    document_type: string;
    link: string;
    uploaded_by?: number;
    file_size?: number;
    file_hash?: string;
    status?: string;
  }): Promise<any> {
    return this.fetchWithErrorHandling<any>(apiUrl("/documents"), {
      method: "POST", 
      body: JSON.stringify(data),
    });
  }

  async createProcessedDocument(data: {
    document_id: number;
    suggested_tags?: Array<{ tag: string; score: number }>;
    model_id?: number;
    threshold_pct?: number;
    ocr_used?: boolean;
    processing_ms?: number;
    company?: number;
  }): Promise<any> {
    return this.fetchWithErrorHandling<any>(apiUrl("/documents/processed"), {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
}

// ---------- Frontend types & helpers ----------
export interface Document {
  id: string;
  name: string;
  uploadDate: string;
  tags: string[];
  size: string;
  type: string;
  link: string;
  company: number | null;
  companyName: string | null;
  uploaded_by: number | null;
  status: string;
  modelGeneratedTags: Array<{ tag: string; score: number; isConfirmed: boolean }>;
  userAddedTags: string[];
}

export function transformBackendDocument(processedDoc: BackendProcessedDocument): Document {
  const tags: string[] = [];
  const modelGeneratedTags: Array<{ tag: string; score: number; isConfirmed: boolean }> = [];
  const userAddedTags: string[] = [];

  if (processedDoc.suggested_tags) {
    processedDoc.suggested_tags.forEach((t) => {
      const isConfirmed = processedDoc.confirmed_tags?.includes(t.tag) || false;
      modelGeneratedTags.push({ tag: t.tag, score: t.score, isConfirmed });
      if (isConfirmed && !tags.includes(t.tag)) tags.push(t.tag);
    });
  }

  if (processedDoc.user_added_labels) {
    processedDoc.user_added_labels.forEach((l) => {
      userAddedTags.push(l);
      if (!tags.includes(l)) tags.push(l);
    });
  }

  if (processedDoc.confirmed_tags) {
    processedDoc.confirmed_tags.forEach((ct) => {
      if (!tags.includes(ct)) tags.push(ct);
    });
  }

  const sizeEstimate = processedDoc.raw_documents?.file_size
    ? formatFileSize(processedDoc.raw_documents.file_size)
    : estimateFileSize(processedDoc.raw_documents?.document_type || "PDF");

  return {
    id: processedDoc.document_id.toString(),
    name: processedDoc.raw_documents?.document_name || "Unknown Document",
    uploadDate: processedDoc.raw_documents?.upload_date.split("T")[0] || "",
    tags,
    size: sizeEstimate,
    type: processedDoc.raw_documents?.document_type || "PDF",
    link: processedDoc.raw_documents?.link || "",
    company: processedDoc.company, // Company is now in processed_documents
    companyName: processedDoc.raw_documents?.companies?.company_name || null,
    uploaded_by: processedDoc.raw_documents?.uploaded_by,
    status: processedDoc.status || "processed",
    modelGeneratedTags,
    userAddedTags,
  };
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function estimateFileSize(documentType: string): string {
  const estimates: { [key: string]: string } = {
    PDF: `${(Math.random() * 4 + 1).toFixed(1)} MB`,
    DOCX: `${(Math.random() * 2 + 0.5).toFixed(1)} MB`,
    XLSX: `${(Math.random() * 5 + 2).toFixed(1)} MB`,
    DOC: `${(Math.random() * 2 + 0.5).toFixed(1)} MB`,
    XLS: `${(Math.random() * 5 + 2).toFixed(1)} MB`,
    TXT: `${(Math.random() * 0.5 + 0.1).toFixed(1)} MB`,
  };
  return estimates[documentType.toUpperCase()] || `${(Math.random() * 3 + 1).toFixed(1)} MB`;
}

// Export singleton
export const apiClient = new APIClient();