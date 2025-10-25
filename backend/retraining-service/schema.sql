-- Retraining Data Table Schema
-- This table stores document text and confirmed tag hierarchies for model retraining

CREATE TABLE public.retraining_data (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL,
  document_text TEXT NOT NULL,
  primary_tag_id INTEGER NULL,
  secondary_tag_id INTEGER NULL,
  tertiary_tag_id INTEGER NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Foreign key constraints
  -- Note: We reference raw_documents(document_id) instead of processed_documents
  -- because processed_documents.document_id is not unique (multiple processing runs per document)
  CONSTRAINT retraining_data_document_id_fkey
    FOREIGN KEY (document_id)
    REFERENCES raw_documents(document_id)
    ON DELETE CASCADE,

  CONSTRAINT retraining_data_primary_tag_fkey
    FOREIGN KEY (primary_tag_id)
    REFERENCES tags(id)
    ON DELETE SET NULL,

  CONSTRAINT retraining_data_secondary_tag_fkey
    FOREIGN KEY (secondary_tag_id)
    REFERENCES tags(id)
    ON DELETE SET NULL,

  CONSTRAINT retraining_data_tertiary_tag_fkey
    FOREIGN KEY (tertiary_tag_id)
    REFERENCES tags(id)
    ON DELETE SET NULL
) TABLESPACE pg_default;

-- Index for faster lookups by document_id
CREATE INDEX idx_retraining_data_document_id ON public.retraining_data(document_id);

-- Index for faster lookups by tag combinations (for analytics/reporting)
CREATE INDEX idx_retraining_data_tags ON public.retraining_data(primary_tag_id, secondary_tag_id, tertiary_tag_id);

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
COMMENT ON TABLE public.retraining_data IS 'Stores document text and confirmed tag hierarchies for AI model retraining';
COMMENT ON COLUMN public.retraining_data.document_id IS 'Reference to processed_documents table';
COMMENT ON COLUMN public.retraining_data.document_text IS 'Full extracted text from the document';
COMMENT ON COLUMN public.retraining_data.primary_tag_id IS 'Primary classification tag ID from tags table';
COMMENT ON COLUMN public.retraining_data.secondary_tag_id IS 'Secondary classification tag ID from tags table';
COMMENT ON COLUMN public.retraining_data.tertiary_tag_id IS 'Tertiary classification tag ID from tags table';
