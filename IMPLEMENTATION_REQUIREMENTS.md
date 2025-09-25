# Implementation Requirements - Removed Mock Data

This document outlines the mock data that has been removed from the Clerc application and what needs to be properly implemented.

## ⚠️ CRITICAL: Services That Need Implementation

### 1. Text Extraction Service (CRITICAL)
**File:** `frontend/components/upload-modal.tsx:167-171`
**Issue:** Text extraction now throws an error instead of using placeholder text
**Required Implementation:**
- Integrate with an OCR service (e.g., AWS Textract, Google Document AI, Azure Form Recognizer)
- Support for PDF, DOCX, XLSX, and other document formats
- Return actual extracted text for document classification
- Handle extraction errors gracefully

### 2. File Size Data (HIGH PRIORITY)
**File:** `frontend/lib/api.ts:292`
**Issue:** File sizes now show "Size unavailable" instead of random estimates
**Required Implementation:**
- Ensure backend properly stores and returns actual file sizes
- Update document upload process to capture real file size metadata
- Verify database schema includes file_size field

### 3. Document Explanations Service (HIGH PRIORITY)
**File:** `frontend/components/document-details-modal.tsx:112-113`
**Issue:** No explanations are shown when API fails (no fallback)
**Required Implementation:**
- Fix `/documents/{id}/explanations` API endpoint reliability
- Ensure explanation data includes proper source_service and classification_level
- Implement proper error handling and retry mechanisms

### 4. Confidence Threshold Configuration (MEDIUM PRIORITY)
**File:** `frontend/lib/api.ts:223-228`
**Issue:** Confidence threshold updates now throw error instead of using localStorage
**Required Implementation:**
- Implement PUT endpoint `/prediction/config` in prediction service
- Add database support for storing confidence thresholds
- Enable real-time threshold updates across the system

### 5. Document Processing Error Handling (HIGH PRIORITY)
**File:** `frontend/app/page.tsx:156-167`
**Issue:** Tag confirmation now fails completely if processed document doesn't exist
**Required Implementation:**
- Ensure document upload workflow creates processed document entries
- Fix database integrity issues between raw_documents and processed_documents
- Implement proper error recovery mechanisms

## 🚨 Immediate Actions Required

1. **Text Extraction Service** - Without this, document classification cannot work
2. **File Size Handling** - Ensure backend returns actual file sizes
3. **Explanation Service Stability** - Fix API reliability issues
4. **Database Integrity** - Ensure consistent document processing workflow

## 📋 Error Messages Now Shown to Users

When these services are missing, users will see detailed error messages instead of mock data:

- **Text Extraction:** "Text extraction service is not implemented. Cannot extract text from {filename}..."
- **Confidence Thresholds:** "Confidence threshold update service is not implemented. Backend API endpoint..."
- **Tag Updates:** "Failed to update document tags: {error}. Document ID: {id}..."
- **Explanations:** Detailed error banner with bullet points explaining missing data

## 🧹 Removed Mock Data

- ❌ Random file size generation (`Math.random()` based estimates)
- ❌ Placeholder text extraction for documents
- ❌ Mock explanations when API fails
- ❌ localStorage fallback for confidence thresholds
- ❌ Automatic processed document creation on failures
- ❌ Default values like "Unknown Document", "PDF" type defaults

## ✅ Legitimate Data That Remains

- ✅ Form placeholders for user input ("Enter your email", etc.)
- ✅ Loading states and empty state messages
- ✅ Environment-based configuration (dev vs prod URLs)
- ✅ Random retry delays and ML training random states
- ✅ UI component styling defaults

## 🔧 Testing Files

The following test files remain as they test real APIs:
- `frontend/test-api.js` - Tests actual API connectivity
- `frontend/test-pagination.js` - Tests real pagination functionality

## 📁 Placeholder Assets To Remove

Consider removing these placeholder files from production:
- `frontend/public/placeholder-logo.png`
- `frontend/public/placeholder-logo.svg`
- `frontend/public/placeholder-user.jpg`
- `frontend/public/placeholder.jpg`
- `frontend/public/placeholder.svg`

## 🎯 Next Steps

1. Prioritize text extraction service implementation
2. Fix document processing workflow integrity
3. Implement missing API endpoints
4. Test error handling with proper error messages
5. Remove placeholder assets
6. Update documentation with real service requirements

---

**Note:** All mock data has been replaced with descriptive error messages that guide developers toward proper implementation.