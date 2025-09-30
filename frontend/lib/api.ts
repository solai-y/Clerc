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

  async getCompleteDocument(id: number): Promise<BackendProcessedDocument> {
    return this.fetchWithErrorHandling<BackendProcessedDocument>(apiUrl(`/documents/${id}/complete`));
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
      confirmed_tags?: string[] | any; // Support both legacy array and new JSONB format
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
    explanations?: Array<{
      level: string;
      tag: string;
      confidence: number;
      reasoning?: string;
      source: string;
    }>;
    prediction_response?: any;
  }): Promise<any> {
    return this.fetchWithErrorHandling<any>(apiUrl("/documents/processed"), {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getDocumentExplanations(documentId: number): Promise<Array<{
    explanation_id: number;
    document_id: number;
    classification_level: string;
    predicted_tag: string;
    confidence: number;
    reasoning: string;
    source_service: string;
    service_response: any;
    created_at: string;
  }>> {
    return this.fetchWithErrorHandling<Array<any>>(apiUrl(`/documents/${documentId}/explanations`));
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
    
    try {
      const response = await this.fetchWithErrorHandling<{
        primary: number;
        secondary: number;
        tertiary: number;
        updated_by: string;
      }>(apiUrl("/predict/config/thresholds"), {
        method: "PUT",
        body: JSON.stringify(updateData),
      });
      
      return {
        success: true,
        message: `Confidence thresholds updated successfully. Primary: ${response.primary}, Secondary: ${response.secondary}, Tertiary: ${response.tertiary}`
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      throw new Error(
        `Failed to update confidence thresholds: ${errorMessage}. ` +
        `Please check that the prediction service is running and the database is accessible. ` +
        `If the issue persists, verify the /predict/config/thresholds endpoint is properly configured.`
      );
    }
  }

  async getConfidenceThresholds(): Promise<{
    primary: number;
    secondary: number;
    tertiary: number;
  }> {
    try {
      const response = await this.fetchWithErrorHandling<{
        primary: number;
        secondary: number;
        tertiary: number;
        updated_at?: string;
        updated_by?: string;
      }>(apiUrl("/predict/config/thresholds"));
      
      return {
        primary: response.primary,
        secondary: response.secondary,
        tertiary: response.tertiary
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      throw new Error(
        `Failed to retrieve confidence thresholds: ${errorMessage}. ` +
        `Please check that the prediction service is running and the database is accessible. ` +
        `If the issue persists, verify the /predict/config/thresholds endpoint is properly configured.`
      );
    }
  }

  // -------- PDF Text Extraction Methods --------
  async extractTextFromPDF(pdfUrl: string): Promise<{
    text: string;
    page_count: number;
    character_count: number;
  }> {
    try {
      const response = await this.fetchWithErrorHandling<{
        text: string;
        page_count: number;
        character_count: number;
      }>(apiUrl("/predict/extract/pdf"), {
        method: "POST",
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      throw new Error(
        `Failed to extract text from PDF: ${errorMessage}. ` +
        `Please check that the prediction service is running and the PDF is accessible. ` +
        `If the issue persists, verify the PDF is not encrypted or image-based.`
      );
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
  // Hierarchical tags
  primaryTag?: { tag: string; source: string; confidence: number };
  secondaryTag?: { tag: string; source: string; confidence: number };
  tertiaryTag?: { tag: string; source: string; confidence: number };
}

export function transformBackendDocument(processedDoc: BackendProcessedDocument): Document {
  console.log('🔍 [API Transform] Processing document:', {
    document_id: processedDoc.document_id,
    document_name: processedDoc.raw_documents?.document_name,
    confirmed_tags_raw: processedDoc.confirmed_tags,
    suggested_tags: processedDoc.suggested_tags,
    user_added_labels: processedDoc.user_added_labels
  });

  const tags: string[] = [];
  const modelGeneratedTags: Array<{ tag: string; score: number; isConfirmed: boolean }> = [];
  const userAddedTags: string[] = [];

  // Extract hierarchical tags from new JSONB format
  let primaryTag: { tag: string; source: string; confidence: number } | undefined;
  let secondaryTag: { tag: string; source: string; confidence: number } | undefined;
  let tertiaryTag: { tag: string; source: string; confidence: number } | undefined;

  // Process the new JSONB confirmed_tags structure
  const processConfirmedTags = (confirmedTagsObj: any): string[] => {
    console.log('🏷️ [API Transform] Processing confirmed_tags:', confirmedTagsObj);

    if (!confirmedTagsObj) {
      console.log('❌ [API Transform] No confirmed_tags found');
      return [];
    }

    // The structure should be: {confirmed_tags: {tags: [...]}}
    // But we receive: confirmedTagsObj = {confirmed_tags: {tags: [...]}}
    const tagsArray = confirmedTagsObj.confirmed_tags?.tags;

    if (!tagsArray || !Array.isArray(tagsArray)) {
      console.log('❌ [API Transform] Invalid structure - expected confirmed_tags.tags array:', confirmedTagsObj);
      return [];
    }

    console.log('🆕 [API Transform] Found tags array:', tagsArray);

    // Process hierarchical tags from JSONB format
    tagsArray.forEach((tagObj: any) => {
      console.log('🔍 [API Transform] Processing tag object:', tagObj);

      if (tagObj.level === 'primary') {
        primaryTag = {
          tag: tagObj.tag,
          source: tagObj.source || 'unknown',
          confidence: tagObj.confidence || 0
        };
        console.log('🔵 [API Transform] Found primary tag:', primaryTag);
      } else if (tagObj.level === 'secondary') {
        secondaryTag = {
          tag: tagObj.tag,
          source: tagObj.source || 'unknown',
          confidence: tagObj.confidence || 0
        };
        console.log('🟢 [API Transform] Found secondary tag:', secondaryTag);
      } else if (tagObj.level === 'tertiary') {
        tertiaryTag = {
          tag: tagObj.tag,
          source: tagObj.source || 'unknown',
          confidence: tagObj.confidence || 0
        };
        console.log('🟠 [API Transform] Found tertiary tag:', tertiaryTag);
      }
    });

    const tagNames = tagsArray.map((t: any) => t.tag);
    console.log('📝 [API Transform] Extracted tag names:', tagNames);
    return tagNames;
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

  // Add confirmed tags to the tags array
  confirmedTagNames.forEach((ct) => {
    if (!tags.includes(ct)) tags.push(ct);
  });

  console.log('📊 [API Transform] Final tag processing results:', {
    document_id: processedDoc.document_id,
    legacy_tags: tags,
    primaryTag,
    secondaryTag,
    tertiaryTag,
    userAddedTags,
    modelGeneratedTags: modelGeneratedTags.length
  });

  const sizeEstimate = processedDoc.raw_documents?.file_size
    ? formatFileSize(processedDoc.raw_documents.file_size)
    : "Size unavailable";

  const transformedDocument = {
    id: processedDoc.document_id.toString(),
    name: processedDoc.raw_documents?.document_name || "[Document name unavailable]",
    uploadDate: processedDoc.raw_documents?.upload_date.split("T")[0] || "[Date unavailable]",
    tags,
    size: sizeEstimate,
    type: processedDoc.raw_documents?.document_type || "[Type unavailable]",
    link: processedDoc.raw_documents?.link || "",
    company: processedDoc.company, // Company is now in processed_documents
    companyName: processedDoc.raw_documents?.companies?.company_name || null,
    uploaded_by: processedDoc.raw_documents?.uploaded_by,
    status: processedDoc.status || "processed",
    modelGeneratedTags,
    userAddedTags,
    // Hierarchical tags
    primaryTag,
    secondaryTag,
    tertiaryTag,
  };

  console.log('✅ [API Transform] Transformed document:', {
    id: transformedDocument.id,
    name: transformedDocument.name,
    tags: transformedDocument.tags,
    primaryTag: transformedDocument.primaryTag,
    secondaryTag: transformedDocument.secondaryTag,
    tertiaryTag: transformedDocument.tertiaryTag,
    userAddedTags: transformedDocument.userAddedTags
  });

  return transformedDocument;
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