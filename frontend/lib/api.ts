// api.ts - Frontend API client for document management

// ---------- Build URLs correctly ----------
const isServer = typeof window === "undefined";
// On the server (SSR), talk to the real backend origin.
// On the client (browser), ALWAYS prepend /api so Next.js rewrites proxy it.
const SERVER_BACKEND_ORIGIN =
  process.env.BACKEND_ORIGIN || "http://localhost";

function apiUrl(path: string) {
  return isServer ? `${SERVER_BACKEND_ORIGIN}${path}` : `/api${path}`;
}

// ---------- Types from backend ----------
export interface BackendProcessedDocument {
  process_id: number;
  document_id: number;
  model_id: number | null;
  threshold_pct: number;
  confirmed_tags: string[] | any | null; // Support both legacy array and new JSONB format
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
  sortBy?: "name" | "date" | "size";
  sortOrder?: "asc" | "desc";
  status?: string;
  companyId?: number;
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
      console.error(`❌ [api] Error for ${displayUrl}:`, error);
      throw error;
    }
  }

  // -------- Document Service Methods (all use relative paths on client) --------
  async getDocuments(options: GetDocumentsOptions = {}): Promise<{
    documents: BackendProcessedDocument[];
    pagination: { total: number; page: number; totalPages: number; limit: number; offset: number };
  }> {
    const params = new URLSearchParams();
    if (options.limit != null) params.append("limit", String(options.limit));
    if (options.offset != null) params.append("offset", String(options.offset));
    if (options.search) params.append("search", options.search);
    if (options.status) params.append("status", options.status);
    if (options.companyId != null) params.append("company_id", String(options.companyId));
    if (options.sortBy) params.append("sort_by", options.sortBy);
    if (options.sortOrder) params.append("sort_order", options.sortOrder);

    const url = apiUrl(`/documents${params.toString() ? `?${params}` : ""}`);

    console.log("[api] GET /documents with params:", {
      ...options,
      finalUrl: url
    });

    const responseData = await this.fetchWithErrorHandling<{
      documents: BackendProcessedDocument[];
      pagination: { total: number; page: number; totalPages: number; limit: number; offset: number };
    }>(url);

    console.log("[api] GET /documents response:", {
      returned: responseData.documents?.length ?? 0,
      pagination: responseData.pagination
    });

    return responseData;
  }

  async getDocument(id: number): Promise<BackendProcessedDocument> {
    const url = apiUrl(`/documents/${id}`);
    return this.fetchWithErrorHandling<BackendProcessedDocument>(url);
  }

  async getCompleteDocument(id: number): Promise<BackendProcessedDocument> {
    const url = apiUrl(`/documents/${id}/complete`);
    return this.fetchWithErrorHandling<BackendProcessedDocument>(url);
  }

  async createDocument(
    document: Omit<BackendProcessedDocument, "process_id" | "processing_date">
  ): Promise<BackendProcessedDocument> {
    const url = apiUrl("/documents");
    return this.fetchWithErrorHandling<BackendProcessedDocument>(url, {
      method: "POST",
      body: JSON.stringify(document),
    });
  }

  async updateDocument(
    id: number,
    document: Partial<Omit<BackendProcessedDocument, "process_id">>
  ): Promise<BackendProcessedDocument> {
    const url = apiUrl(`/documents/${id}`);
    return this.fetchWithErrorHandling<BackendProcessedDocument>(url, {
      method: "PUT",
      body: JSON.stringify(document),
    });
  }

  async deleteDocument(id: number): Promise<void> {
    const url = apiUrl(`/documents/${id}`);
    await this.fetchWithErrorHandling<null>(url, { method: "DELETE" });
  }

  async updateDocumentTags(
    documentId: number,
    tagData: {
      confirmed_tags?: string[] | any;
      user_added_labels?: string[];
      user_removed_tags?: string[];
    }
  ): Promise<BackendProcessedDocument> {
    const url = apiUrl(`/documents/${documentId}/tags`);
    return this.fetchWithErrorHandling<BackendProcessedDocument>(url, {
      method: "PATCH",
      body: JSON.stringify(tagData),
    });
  }

  async getUnprocessedDocuments(limit: number = 1): Promise<{
    unprocessed_documents: any[];
    count: number;
  }> {
    const url = apiUrl(`/documents/unprocessed?limit=${limit}`);
    return this.fetchWithErrorHandling<{ unprocessed_documents: any[]; count: number }>(url);
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
    const url = apiUrl("/documents");
    return this.fetchWithErrorHandling<any>(url, {
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
    explanations?: Array<{
      level: string;
      tag: string;
      confidence: number;
      reasoning?: string;
      source: string;
    }>;
    prediction_response?: any;
  }): Promise<any> {
    const url = apiUrl("/documents/processed");
    return this.fetchWithErrorHandling<any>(url, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getDocumentExplanations(documentId: number): Promise<
    Array<{
      explanation_id: number;
      document_id: number;
      classification_level: string;
      predicted_tag: string;
      confidence: number;
      reasoning: string;
      source_service: string;
      service_response: any;
      created_at: string;
    }>
  > {
    const url = apiUrl(`/documents/${documentId}/explanations`);
    return this.fetchWithErrorHandling<Array<any>>(url);
  }

  // -------- Prediction Service Configuration Methods --------
  async updateConfidenceThresholds(thresholds: {
    primary?: number;
    secondary?: number;
    tertiary?: number;
  }): Promise<{ success: boolean; message: string }> {
    const updateData: any = { updated_by: "frontend_user" };
    if (thresholds.primary !== undefined) updateData.primary = thresholds.primary;
    if (thresholds.secondary !== undefined) updateData.secondary = thresholds.secondary;
    if (thresholds.tertiary !== undefined) updateData.tertiary = thresholds.tertiary;

    const url = apiUrl("/predict/config/thresholds");

    try {
      const response = await this.fetchWithErrorHandling<{
        primary: number;
        secondary: number;
        tertiary: number;
        updated_by: string;
      }>(url, { method: "PUT", body: JSON.stringify(updateData) });

      return {
        success: true,
        message: `Confidence thresholds updated successfully.`,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      throw new Error(`Failed to update confidence thresholds: ${errorMessage}.`);
    }
  }

  async getConfidenceThresholds(): Promise<{
    primary: number;
    secondary: number;
    tertiary: number;
  }> {
    const url = apiUrl("/predict/config/thresholds");
    try {
      return await this.fetchWithErrorHandling<{
        primary: number;
        secondary: number;
        tertiary: number;
      }>(url);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      throw new Error(`Failed to retrieve confidence thresholds: ${errorMessage}.`);
    }
  }

  // -------- PDF Text Extraction Methods --------
  async extractTextFromPDF(pdfUrl: string): Promise<{
    text: string;
    page_count: number;
    character_count: number;
  }> {
    const url = apiUrl("/predict/extract/pdf");
    try {
      return await this.fetchWithErrorHandling<{
        text: string;
        page_count: number;
        character_count: number;
      }>(url, { method: "POST", body: JSON.stringify({ pdf_url: pdfUrl }) });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      throw new Error(`Failed to extract text from PDF: ${errorMessage}.`);
    }
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
  primaryTag?: { tag: string; source: string; confidence: number };
  secondaryTag?: { tag: string; source: string; confidence: number };
  tertiaryTag?: { tag: string; source: string; confidence: number };
}

export function transformBackendDocument(processedDoc: BackendProcessedDocument): Document {
  const tags: string[] = [];
  const modelGeneratedTags: Array<{ tag: string; score: number; isConfirmed: boolean }> = [];
  const userAddedTags: string[] = [];
  let primaryTag: { tag: string; source: string; confidence: number } | undefined;
  let secondaryTag: { tag: string; source: string; confidence: number } | undefined;
  let tertiaryTag: { tag: string; source: string; confidence: number } | undefined;

  const processConfirmedTags = (confirmedTagsObj: any): string[] => {
    if (!confirmedTagsObj) return [];
    const tagsArray = confirmedTagsObj.confirmed_tags?.tags;
    if (!Array.isArray(tagsArray)) return [];

    tagsArray.forEach((tagObj: any) => {
      if (tagObj.level === 'primary') {
        primaryTag = { tag: tagObj.tag, source: tagObj.source || 'unknown', confidence: tagObj.confidence || 0 };
      } else if (tagObj.level === 'secondary') {
        secondaryTag = { tag: tagObj.tag, source: tagObj.source || 'unknown', confidence: tagObj.confidence || 0 };
      } else if (tagObj.level === 'tertiary') {
        tertiaryTag = { tag: tagObj.tag, source: tagObj.source || 'unknown', confidence: tagObj.confidence || 0 };
      }
    });

    return tagsArray.map((t: any) => t.tag);
  };

  const confirmedTagNames = processConfirmedTags(processedDoc.confirmed_tags);

  if (processedDoc.suggested_tags) {
    processedDoc.suggested_tags.forEach((t) => {
      const isConfirmed = confirmedTagNames.includes(t.tag);
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

  confirmedTagNames.forEach((ct) => {
    if (!tags.includes(ct)) tags.push(ct);
  });

  const sizeEstimate = processedDoc.raw_documents?.file_size
    ? formatFileSize(processedDoc.raw_documents.file_size)
    : "Size unavailable";

  return {
    id: processedDoc.document_id.toString(),
    name: processedDoc.raw_documents?.document_name || "[Document name unavailable]",
    uploadDate: processedDoc.raw_documents?.upload_date.split("T")[0] || "[Date unavailable]",
    tags,
    size: sizeEstimate,
    type: processedDoc.raw_documents?.document_type || "[Type unavailable]",
    link: processedDoc.raw_documents?.link || "",
    company: processedDoc.company,
    companyName: processedDoc.raw_documents?.companies?.company_name || null,
    uploaded_by: processedDoc.raw_documents?.uploaded_by,
    status: processedDoc.status || "processed",
    modelGeneratedTags,
    userAddedTags,
    primaryTag,
    secondaryTag,
    tertiaryTag,
  };
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// Export singleton
export const apiClient = new APIClient();