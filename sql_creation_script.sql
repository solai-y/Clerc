-- Confidence Threshold Table
create table public.confidence_thresholds (
  id serial not null,
  primary_threshold numeric(4, 3) not null default 0.85,
  secondary_threshold numeric(4, 3) not null default 0.80,
  tertiary_threshold numeric(4, 3) not null default 0.75,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  updated_by text null default 'system'::text,
  constraint confidence_thresholds_pkey primary key (id)
) TABLESPACE pg_default;

create trigger update_confidence_thresholds_updated_at_trigger BEFORE
update on confidence_thresholds for EACH row
execute FUNCTION update_confidence_thresholds_updated_at ();

-- Raw Documents Table
create table public.raw_documents (
  document_id bigint generated always as identity not null,
  document_name text not null,
  document_type text not null,
  link text not null,
  uploaded_by bigint null,
  upload_date timestamp with time zone null default now(),
  file_size bigint null,
  file_hash text null,
  status text null default 'uploaded'::text,
  constraint raw_documents_pkey primary key (document_id),
  constraint raw_documents_uploaded_by_fkey foreign KEY (uploaded_by) references access_control (access_id) on delete set null
) TABLESPACE pg_default;

create index IF not exists idx_raw_documents_upload_date on public.raw_documents using btree (upload_date) TABLESPACE pg_default;

create index IF not exists idx_raw_documents_status on public.raw_documents using btree (status) TABLESPACE pg_default;

create index IF not exists idx_raw_documents_file_hash on public.raw_documents using btree (file_hash) TABLESPACE pg_default;

-- Processed Documents Table
create table public.processed_documents (
  process_id bigint generated always as identity not null,
  document_id bigint null,
  model_id bigint null,
  threshold_pct integer null default 60,
  suggested_tags jsonb null,
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
  company bigint null,
  confirmed_tags jsonb null,
  constraint processed_documents_pkey primary key (process_id),
  constraint processed_documents_company_fkey foreign KEY (company) references companies (company_id) on delete set null,
  constraint processed_documents_document_id_fkey foreign KEY (document_id) references raw_documents (document_id) on delete CASCADE,
  constraint processed_documents_model_id_fkey foreign KEY (model_id) references model_versions (model_id) on delete set null,
  constraint processed_documents_user_id_fkey foreign KEY (user_id) references access_control (access_id)
) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_company on public.processed_documents using btree (company) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_document_id on public.processed_documents using btree (document_id) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_model_id on public.processed_documents using btree (model_id) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_processing_date on public.processed_documents using btree (processing_date) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_status on public.processed_documents using btree (status) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_user_reviewed on public.processed_documents using btree (user_reviewed) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_user_id on public.processed_documents using btree (user_id) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_suggested_tags on public.processed_documents using gin (suggested_tags) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_user_added_labels on public.processed_documents using gin (user_added_labels) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_errors on public.processed_documents using gin (errors) TABLESPACE pg_default;

create index IF not exists idx_processed_documents_confirmed_tags on public.processed_documents using gin (confirmed_tags) TABLESPACE pg_default;

-- Explainations Table
create table public.explanations (
  explanation_id serial not null,
  process_id integer not null,
  classification_level character varying(20) not null,
  predicted_tag character varying(255) not null,
  confidence numeric(5, 3) not null,
  reasoning text null,
  source_service character varying(10) not null,
  service_response jsonb null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint explanations_pkey primary key (explanation_id),
  constraint fk_explanations_process_id foreign KEY (process_id) references processed_documents (process_id) on delete CASCADE,
  constraint explanations_classification_level_check check (
    (
      (classification_level)::text = any (
        (
          array[
            'primary'::character varying,
            'secondary'::character varying,
            'tertiary'::character varying
          ]
        )::text[]
      )
    )
  ),
  constraint explanations_confidence_check check (
    (
      (confidence >= (0)::numeric)
      and (confidence <= (1)::numeric)
    )
  ),
  constraint explanations_source_service_check check (
    (
      (source_service)::text = any (
        (
          array['ai'::character varying, 'llm'::character varying]
        )::text[]
      )
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_explanations_process_id on public.explanations using btree (process_id) TABLESPACE pg_default;

create index IF not exists idx_explanations_level on public.explanations using btree (classification_level) TABLESPACE pg_default;

create index IF not exists idx_explanations_source on public.explanations using btree (source_service) TABLESPACE pg_default;

create index IF not exists idx_explanations_created_at on public.explanations using btree (created_at) TABLESPACE pg_default;

create trigger trigger_explanations_updated_at BEFORE
update on explanations for EACH row
execute FUNCTION update_explanations_updated_at ();

-- Retraining data table
create table public.retraining_data (
  id serial not null,
  document_id integer null,
  document_text text not null,
  primary_tag_ids integer[] null,
  secondary_tag_ids integer[] null,
  tertiary_tag_ids integer[] null,
  created_at timestamp without time zone null default now(),
  updated_at timestamp without time zone null default now(),
  constraint retraining_data_pkey primary key (id),
  constraint retraining_data_document_id_fkey foreign KEY (document_id) references raw_documents (document_id) on delete CASCADE deferrable initially DEFERRED
) TABLESPACE pg_default;

create index IF not exists idx_retraining_data_document_id on public.retraining_data using btree (document_id) TABLESPACE pg_default;

create index IF not exists idx_retraining_data_updated_at on public.retraining_data using btree (updated_at) TABLESPACE pg_default;

create index IF not exists idx_retraining_data_primary_tags on public.retraining_data using gin (primary_tag_ids) TABLESPACE pg_default;

create index IF not exists idx_retraining_data_secondary_tags on public.retraining_data using gin (secondary_tag_ids) TABLESPACE pg_default;

create index IF not exists idx_retraining_data_tertiary_tags on public.retraining_data using gin (tertiary_tag_ids) TABLESPACE pg_default;

create trigger trigger_update_retraining_data_updated_at BEFORE
update on retraining_data for EACH row
execute FUNCTION update_retraining_data_updated_at ();

-- tags table
create table public.tags (
  id serial not null,
  tag_name text not null,
  parent_id integer null,
  constraint tags_pkey primary key (id),
  constraint tags_parent_id_fkey foreign KEY (parent_id) references tags (id) on delete CASCADE
) TABLESPACE pg_default;

create trigger trigger_update_confirmed_tags
after
update OF tag_name on tags for EACH row
execute FUNCTION update_confirmed_tags_on_tagname_change ();


-- Users Table
create table public.users (
  id uuid not null,
  email text not null,
  full_name text null,
  avatar_url text null,
  role text null default 'user'::text,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint users_pkey primary key (id),
  constraint users_email_key unique (email),
  constraint users_id_fkey foreign KEY (id) references auth.users (id),
  constraint users_role_check check ((role = any (array['user'::text, 'admin'::text])))
) TABLESPACE pg_default;

create index IF not exists idx_users_email on public.users using btree (email) TABLESPACE pg_default;

create trigger update_users_updated_at BEFORE
update on users for EACH row
execute FUNCTION update_updated_at_column ();

-- Company table
create table public.companies (
  company_id bigint generated always as identity not null,
  company_name text not null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint companies_pkey primary key (company_id)
) TABLESPACE pg_default;

-- Access Logs table
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

-- Logs table
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

-- Model version table
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

