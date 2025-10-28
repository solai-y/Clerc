-- Retraining Data Table Schema
-- This table stores document text and confirmed tags (multiple tags per level) for model retraining

CREATE TABLE public.retraining_data (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL,
  document_text TEXT NOT NULL,
  primary_tag_ids INTEGER[] NULL,  -- Array of primary tag IDs
  secondary_tag_ids INTEGER[] NULL,  -- Array of secondary tag IDs
  tertiary_tag_ids INTEGER[] NULL,  -- Array of tertiary tag IDs
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Foreign key constraint for document
  -- Note: We reference raw_documents(document_id) instead of processed_documents
  -- because processed_documents.document_id is not unique (multiple processing runs per document)
  CONSTRAINT retraining_data_document_id_fkey
    FOREIGN KEY (document_id)
    REFERENCES raw_documents(document_id)
    ON DELETE CASCADE

  -- Note: Foreign key constraints cannot be directly applied to array elements
  -- Tag ID validation will be handled in application logic
) TABLESPACE pg_default;

-- Index for faster lookups by document_id
CREATE INDEX idx_retraining_data_document_id ON public.retraining_data(document_id);

-- GIN indexes for efficient array searches
CREATE INDEX idx_retraining_data_primary_tags ON public.retraining_data USING GIN (primary_tag_ids);
CREATE INDEX idx_retraining_data_secondary_tags ON public.retraining_data USING GIN (secondary_tag_ids);
CREATE INDEX idx_retraining_data_tertiary_tags ON public.retraining_data USING GIN (tertiary_tag_ids);

-- Index for faster lookups by timestamps
CREATE INDEX idx_retraining_data_updated_at ON public.retraining_data(updated_at);

-- Trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_retraining_data_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_retraining_data_updated_at
BEFORE UPDATE ON public.retraining_data
FOR EACH ROW
EXECUTE FUNCTION update_retraining_data_updated_at();

-- Comments for documentation
COMMENT ON TABLE public.retraining_data IS 'Stores document text and confirmed tags for AI model retraining';
COMMENT ON COLUMN public.retraining_data.document_id IS 'Reference to raw_documents table';
COMMENT ON COLUMN public.retraining_data.document_text IS 'Full extracted text from the document';
COMMENT ON COLUMN public.retraining_data.primary_tag_ids IS 'Array of primary classification tag IDs from tags table';
COMMENT ON COLUMN public.retraining_data.secondary_tag_ids IS 'Array of secondary classification tag IDs from tags table';
COMMENT ON COLUMN public.retraining_data.tertiary_tag_ids IS 'Array of tertiary classification tag IDs from tags table';

-- Migration script (run this if you have existing data)
-- ALTER TABLE public.retraining_data
--   DROP CONSTRAINT IF EXISTS retraining_data_primary_tag_fkey,
--   DROP CONSTRAINT IF EXISTS retraining_data_secondary_tag_fkey,
--   DROP CONSTRAINT IF EXISTS retraining_data_tertiary_tag_fkey;
--
-- ALTER TABLE public.retraining_data
--   ALTER COLUMN primary_tag_id TYPE INTEGER[] USING CASE WHEN primary_tag_id IS NULL THEN NULL ELSE ARRAY[primary_tag_id] END,
--   ALTER COLUMN secondary_tag_id TYPE INTEGER[] USING CASE WHEN secondary_tag_id IS NULL THEN NULL ELSE ARRAY[secondary_tag_id] END,
--   ALTER COLUMN tertiary_tag_id TYPE INTEGER[] USING CASE WHEN tertiary_tag_id IS NULL THEN NULL ELSE ARRAY[tertiary_tag_id] END;
--
-- ALTER TABLE public.retraining_data
--   RENAME COLUMN primary_tag_id TO primary_tag_ids;
-- ALTER TABLE public.retraining_data
--   RENAME COLUMN secondary_tag_id TO secondary_tag_ids;
-- ALTER TABLE public.retraining_data
--   RENAME COLUMN tertiary_tag_id TO tertiary_tag_ids;
--
-- DROP INDEX IF EXISTS idx_retraining_data_tags;
-- CREATE INDEX idx_retraining_data_primary_tags ON public.retraining_data USING GIN (primary_tag_ids);
-- CREATE INDEX idx_retraining_data_secondary_tags ON public.retraining_data USING GIN (secondary_tag_ids);
-- CREATE INDEX idx_retraining_data_tertiary_tags ON public.retraining_data USING GIN (tertiary_tag_ids);
