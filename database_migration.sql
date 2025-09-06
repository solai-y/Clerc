-- Database Migration Script: Remove company requirement from raw_documents and add optional company to processed_documents
-- Execute this in your Supabase SQL editor

-- Step 1: Remove the company column from raw_documents table
-- First, drop the foreign key constraint
ALTER TABLE public.raw_documents DROP CONSTRAINT IF EXISTS raw_documents_company_fkey;

-- Drop the index on company column
DROP INDEX IF EXISTS public.idx_raw_documents_company;

-- Remove the company column
ALTER TABLE public.raw_documents DROP COLUMN IF EXISTS company;

-- Step 2: Add optional company column to processed_documents table
-- Add company column as optional (nullable)
ALTER TABLE public.processed_documents ADD COLUMN IF NOT EXISTS company bigint NULL;

-- Add foreign key constraint to companies table
ALTER TABLE public.processed_documents 
ADD CONSTRAINT processed_documents_company_fkey 
FOREIGN KEY (company) REFERENCES public.companies (company_id) ON DELETE SET NULL;

-- Step 3: Create index for the new company column in processed_documents
CREATE INDEX IF NOT EXISTS idx_processed_documents_company 
ON public.processed_documents USING btree (company);

-- Step 4: Update any existing processed_documents with company info (optional)
-- This query moves company data from raw_documents to processed_documents
-- Note: Run this BEFORE dropping the company column if you want to preserve existing company associations
-- UPDATE public.processed_documents 
-- SET company = rd.company 
-- FROM public.raw_documents rd 
-- WHERE processed_documents.document_id = rd.document_id 
-- AND rd.company IS NOT NULL;

-- Step 5: Make uploaded_by optional in raw_documents (since login isn't implemented)
-- The column is already nullable, but let's ensure it doesn't have a NOT NULL constraint
ALTER TABLE public.raw_documents ALTER COLUMN uploaded_by DROP NOT NULL;

-- Verification queries (uncomment to check the changes):
-- SELECT column_name, is_nullable, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'raw_documents' AND table_schema = 'public';

-- SELECT column_name, is_nullable, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'processed_documents' AND table_schema = 'public';