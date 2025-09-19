-- Create explanations table to store AI/LLM reasoning for document classifications
CREATE TABLE explanations (
    explanation_id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL,  -- References processed_documents.process_id
    classification_level VARCHAR(20) NOT NULL CHECK (classification_level IN ('primary', 'secondary', 'tertiary')),
    predicted_tag VARCHAR(255) NOT NULL,
    confidence DECIMAL(5,3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT,
    source_service VARCHAR(10) NOT NULL CHECK (source_service IN ('ai', 'llm')),
    service_response JSONB,  -- Store full prediction response for debugging
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to processed_documents table
    CONSTRAINT fk_explanations_process_id 
        FOREIGN KEY (process_id) 
        REFERENCES processed_documents(process_id) 
        ON DELETE CASCADE,
        
    -- Ensure unique explanation per processed document per level
    CONSTRAINT uk_explanations_process_level 
        UNIQUE (process_id, classification_level)
);

-- Create indexes for efficient querying
CREATE INDEX idx_explanations_process_id ON explanations(process_id);
CREATE INDEX idx_explanations_level ON explanations(classification_level);
CREATE INDEX idx_explanations_source ON explanations(source_service);
CREATE INDEX idx_explanations_created_at ON explanations(created_at);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_explanations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_explanations_updated_at
    BEFORE UPDATE ON explanations
    FOR EACH ROW
    EXECUTE FUNCTION update_explanations_updated_at();

-- Add comment to table
COMMENT ON TABLE explanations IS 'Stores AI/LLM reasoning and explanations for document classification predictions';
COMMENT ON COLUMN explanations.classification_level IS 'Hierarchical level: primary, secondary, or tertiary';
COMMENT ON COLUMN explanations.predicted_tag IS 'The tag that was predicted for this level';
COMMENT ON COLUMN explanations.confidence IS 'Confidence score from 0.0 to 1.0';
COMMENT ON COLUMN explanations.reasoning IS 'Human-readable explanation from AI/LLM service';
COMMENT ON COLUMN explanations.source_service IS 'Which service provided this explanation: ai or llm';
COMMENT ON COLUMN explanations.service_response IS 'Full JSON response from the service for debugging';