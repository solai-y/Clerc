-- 1. Access Control (unchanged)
create table access_control (
  access_id bigint primary key generated always as identity,
  "user" text not null,
  api_key text not null
);

-- 2. Companies (unchanged)
create table companies (
  company_id bigint primary key generated always as identity,
  company_name text not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 3. Model Versions (unchanged)
create table model_versions (
  model_id bigint primary key generated always as identity,
  model_name text not null,
  version text not null,
  description text,
  deployed_date timestamp with time zone,
  parameters jsonb,
  metrics jsonb
);

-- 4. Raw Documents (REVISED - removed categories, simplified)
create table raw_documents (
  document_id bigint primary key generated always as identity,
  document_name text not null,
  document_type text not null,
  link text not null,
  uploaded_by bigint references access_control(access_id) on delete set null,
  company bigint references companies(company_id) on delete set null,
  upload_date timestamp with time zone default now(),
  file_size bigint,
  file_hash text, -- for duplicate detection
  status text default 'uploaded' -- uploaded, processing, processed, failed
);

-- 5. Processed Documents (MAJOR REVISION - now stores actual prediction results)
create table processed_documents (
  process_id bigint primary key generated always as identity,
  document_id bigint references raw_documents(document_id) on delete cascade,
  model_id bigint references model_versions(model_id) on delete set null,
  
  -- Processing configuration
  threshold_pct integer default 60,
  
  -- Prediction results as denormalized JSON arrays (matching your API response)
  predicted_tags jsonb, -- [{"tag": "news", "score": 0.92}, {"tag": "Recommendations", "score": 0.81}]
  user_labels text[], -- ["Discovery Event", "FY2024"]
  
  -- Processing metadata
  ocr_used boolean default false,
  processing_ms integer,
  processing_date timestamp with time zone default now(),
  
  -- Error handling
  errors text[], -- ["b.txt is not a PDF"]
  
  -- Training data management
  saved_training boolean default false,
  saved_count integer default 0,
  
  -- Request tracking
  request_id text, -- for logs and debugging
  
  -- Overall processing status
  status text default 'processing' -- processing, completed, failed
);

-- 6. Processing Batches (NEW - to handle batch processing requests)
create table processing_batches (
  batch_id bigint primary key generated always as identity,
  request_id text unique not null,
  total_documents integer not null,
  processed_documents integer default 0,
  failed_documents integer default 0,
  threshold_pct integer default 60,
  save_to_training boolean default false,
  created_at timestamp with time zone default now(),
  completed_at timestamp with time zone,
  status text default 'processing' -- processing, completed, partially_failed, failed
);

-- 7. Logs (REVISED - simplified for audit trail)
create table logs (
  log_id bigint primary key generated always as identity,
  action_type text not null, -- upload, process, predict, delete, etc.
  action_date timestamp with time zone default now(),
  document_id bigint references raw_documents(document_id) on delete set null,
  batch_id bigint references processing_batches(batch_id) on delete set null,
  access_id bigint references access_control(access_id) on delete set null,
  request_id text,
  action_details jsonb,
  ip_address text,
  success boolean default true
);

-- 8. Document Access Logs (unchanged but optional)
create table document_access_logs (
  access_id bigint primary key generated always as identity,
  document_id bigint references raw_documents(document_id) on delete cascade,
  access_date timestamp with time zone default now(),
  access_type text,
  ip_address text,
  user_agent text,
  success boolean
);

-- OPTIONAL: If you want to extract tags for analytics/reporting
-- 9. Tag Analytics View (Materialized view for performance)
create materialized view tag_analytics as
select 
  tag_data->>'tag' as tag_name,
  (tag_data->>'score')::float as score,
  count(*) as frequency,
  avg((tag_data->>'score')::float) as avg_score,
  min((tag_data->>'score')::float) as min_score,
  max((tag_data->>'score')::float) as max_score
from processed_documents pd,
     jsonb_array_elements(pd.predicted_tags) as tag_data
group by tag_data->>'tag';

-- Indexes for performance
create index idx_raw_documents_status on raw_documents(status);
create index idx_raw_documents_company on raw_documents(company);
create index idx_raw_documents_upload_date on raw_documents(upload_date);
create index idx_processed_documents_document_id on processed_documents(document_id);
create index idx_processed_documents_model_id on processed_documents(model_id);
create index idx_processed_documents_processing_date on processed_documents(processing_date);
create index idx_processing_batches_request_id on processing_batches(request_id);
create index idx_processing_batches_status on processing_batches(status);
create index idx_logs_request_id on logs(request_id);
create index idx_logs_action_date on logs(action_date);

-- GIN indexes for JSONB and array operations
create index idx_processed_documents_predicted_tags on processed_documents using gin(predicted_tags);
create index idx_processed_documents_user_labels on processed_documents using gin(user_labels);
create index idx_processed_documents_errors on processed_documents using gin(errors);

-- Function to refresh tag analytics (call periodically)
create or replace function refresh_tag_analytics()
returns void as $$
begin
  refresh materialized view tag_analytics;
end;
$$ language plpgsql;