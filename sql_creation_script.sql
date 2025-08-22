create table public.access_control (
  access_id bigint generated always as identity not null,
  "user" text not null,
  api_key text not null,
  constraint access_control_pkey primary key (access_id)
) TABLESPACE pg_default;

create table public.companies (
  company_id bigint generated always as identity not null,
  company_name text not null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint companies_pkey primary key (company_id)
) TABLESPACE pg_default;

create table public.companies (
  company_id bigint generated always as identity not null,
  company_name text not null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint companies_pkey primary key (company_id)
) TABLESPACE pg_default;

create table public.document_access_logs (
  access_id bigint generated always as identity not null,
  document_id bigint null,
  access_date timestamp with time zone null default now(),
  access_type text null,
  ip_address text null,
  user_agent text null,
  success boolean null,
  constraint document_access_logs_pkey primary key (access_id),
  constraint document_access_logs_document_id_fkey foreign KEY (document_id) references raw_documents (document_id) on delete CASCADE
) TABLESPACE pg_default;

create table public.logs (
  log_id bigint generated always as identity not null,
  action_type text not null,
  action_date timestamp with time zone null default now(),
  document_id bigint null,
  access_id bigint null,
  action_details jsonb null,
  batch_id bigint null,
  request_id text null,
  ip_address text null,
  success boolean null default true,
  constraint logs_pkey primary key (log_id),
  constraint logs_access_id_fkey foreign KEY (access_id) references access_control (access_id) on delete set null,
  constraint logs_batch_id_fkey foreign KEY (batch_id) references processing_batches (batch_id) on delete set null,
  constraint logs_document_id_fkey foreign KEY (document_id) references raw_documents (document_id) on delete set null
) TABLESPACE pg_default;

create index IF not exists idx_logs_action_date on public.logs using btree (action_date) TABLESPACE pg_default;

create index IF not exists idx_logs_request_id on public.logs using btree (request_id) TABLESPACE pg_default;

create index IF not exists idx_logs_document_id on public.logs using btree (document_id) TABLESPACE pg_default;

create index IF not exists idx_logs_batch_id on public.logs using btree (batch_id) TABLESPACE pg_default;

create table public.model_versions (
  model_id bigint generated always as identity not null,
  model_name text not null,
  version text not null,
  description text null,
  deployed_date timestamp with time zone null,
  parameters jsonb null,
  metrics jsonb null,
  constraint model_versions_pkey primary key (model_id)
) TABLESPACE pg_default;

create table public.processed_documents (
  process_id bigint generated always as identity not null,
  document_id bigint null,
  model_id bigint null,
  threshold_pct integer null default 60,
  suggested_tags jsonb null,
  confirmed_tags text[] null,
  user_added_labels text[] null,
  user_removed_tags text[] null,
  user_reviewed boolean null default false,
  user_id bigint null,
  reviewed_at timestamp with time zone null,
  ocr_used boolean null default false,
  processing_ms integer null,
  processing_date timestamp with time zone null default now(),
  errors text[] null,
  saved_training boolean null default false,
  saved_count integer null default 0,
  request_id text null,
  status text null default 'api_processed'::text,
  constraint processed_documents_pkey primary key (process_id),
  constraint processed_documents_document_id_fkey foreign KEY (document_id) references raw_documents (document_id) on delete CASCADE,
  constraint processed_documents_model_id_fkey foreign KEY (model_id) references model_versions (model_id) on delete set null,
  constraint processed_documents_user_id_fkey foreign KEY (user_id) references access_control (access_id)
) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_document_id on public.processed_documents using btree (document_id) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_model_id on public.processed_documents using btree (model_id) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_processing_date on public.processed_documents using btree (processing_date) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_status on public.processed_documents using btree (status) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_user_reviewed on public.processed_documents using btree (user_reviewed) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_user_id on public.processed_documents using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_suggested_tags on public.processed_documents using gin (suggested_tags) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_confirmed_tags on public.processed_documents using gin (confirmed_tags) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_user_added_labels on public.processed_documents using gin (user_added_labels) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_errors on public.processed_documents using gin (errors) TABLESPACE pg_default;

create table public.raw_documents (
  document_id bigint generated always as identity not null,
  document_name text not null,
  document_type text not null,
  link text not null,
  uploaded_by bigint null,
  company bigint null,
  upload_date timestamp with time zone null default now(),
  file_size bigint null,
  file_hash text null,
  status text null default 'uploaded'::text,
  constraint raw_documents_pkey primary key (document_id),
  constraint raw_documents_company_fkey foreign KEY (company) references companies (company_id) on delete set null,
  constraint raw_documents_uploaded_by_fkey foreign KEY (uploaded_by) references access_control (access_id) on delete set null
) TABLESPACE pg_default;

create index IF not exists idx_raw_documents_company on public.raw_documents using btree (company) TABLESPACE pg_default;

create index IF not exists idx_raw_documents_upload_date on public.raw_documents using btree (upload_date) TABLESPACE pg_default;

create index IF not exists idx_raw_documents_status on public.raw_documents using btree (status) TABLESPACE pg_default;

create index IF not exists idx_raw_documents_file_hash on public.raw_documents using btree (file_hash) TABLESPACE pg_default;

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