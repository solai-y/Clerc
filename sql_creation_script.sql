-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.access_control (
  access_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user text NOT NULL,
  api_key text NOT NULL,
  CONSTRAINT access_control_pkey PRIMARY KEY (access_id)
);
CREATE TABLE public.companies (
  company_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  company_name text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT companies_pkey PRIMARY KEY (company_id)
);
CREATE TABLE public.confidence_thresholds (
  id integer NOT NULL DEFAULT nextval('confidence_thresholds_id_seq'::regclass),
  primary_threshold numeric NOT NULL DEFAULT 0.85,
  secondary_threshold numeric NOT NULL DEFAULT 0.80,
  tertiary_threshold numeric NOT NULL DEFAULT 0.75,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  updated_by text DEFAULT 'system'::text,
  CONSTRAINT confidence_thresholds_pkey PRIMARY KEY (id)
);
CREATE TABLE public.document_access_logs (
  access_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  document_id bigint,
  access_date timestamp with time zone DEFAULT now(),
  access_type text,
  ip_address text,
  user_agent text,
  success boolean,
  CONSTRAINT document_access_logs_pkey PRIMARY KEY (access_id),
  CONSTRAINT document_access_logs_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.raw_documents(document_id)
);
CREATE TABLE public.explanations (
  explanation_id integer NOT NULL DEFAULT nextval('explanations_explanation_id_seq'::regclass),
  process_id integer NOT NULL,
  classification_level character varying NOT NULL CHECK (classification_level::text = ANY (ARRAY['primary'::character varying, 'secondary'::character varying, 'tertiary'::character varying]::text[])),
  predicted_tag character varying NOT NULL,
  confidence numeric NOT NULL CHECK (confidence >= 0::numeric AND confidence <= 1::numeric),
  reasoning text,
  source_service character varying NOT NULL CHECK (source_service::text = ANY (ARRAY['ai'::character varying, 'llm'::character varying]::text[])),
  service_response jsonb,
  created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT explanations_pkey PRIMARY KEY (explanation_id),
  CONSTRAINT fk_explanations_process_id FOREIGN KEY (process_id) REFERENCES public.processed_documents(process_id)
);
CREATE TABLE public.logs (
  log_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  action_type text NOT NULL,
  action_date timestamp with time zone DEFAULT now(),
  document_id bigint,
  access_id bigint,
  action_details jsonb,
  batch_id bigint,
  request_id text,
  ip_address text,
  success boolean DEFAULT true,
  CONSTRAINT logs_pkey PRIMARY KEY (log_id),
  CONSTRAINT logs_access_id_fkey FOREIGN KEY (access_id) REFERENCES public.access_control(access_id),
  CONSTRAINT logs_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.raw_documents(document_id),
  CONSTRAINT logs_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.processing_batches(batch_id)
);
CREATE TABLE public.model_versions (
  model_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  model_name text NOT NULL,
  version text NOT NULL,
  description text,
  deployed_date timestamp with time zone,
  parameters jsonb,
  metrics jsonb,
  CONSTRAINT model_versions_pkey PRIMARY KEY (model_id)
);
CREATE TABLE public.processed_documents (
  process_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  document_id bigint,
  model_id bigint,
  threshold_pct integer DEFAULT 60,
  suggested_tags jsonb,
  confirmed_tags ARRAY,
  user_added_labels ARRAY,
  user_removed_tags ARRAY,
  user_reviewed boolean DEFAULT false,
  user_id bigint,
  reviewed_at timestamp with time zone,
  ocr_used boolean DEFAULT false,
  processing_ms integer,
  processing_date timestamp with time zone DEFAULT now(),
  errors ARRAY,
  saved_training boolean DEFAULT false,
  saved_count integer DEFAULT 0,
  request_id text,
  status text DEFAULT 'api_processed'::text,
  company bigint,
  CONSTRAINT processed_documents_pkey PRIMARY KEY (process_id),
  CONSTRAINT processed_documents_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.raw_documents(document_id),
  CONSTRAINT processed_documents_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.model_versions(model_id),
  CONSTRAINT processed_documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.access_control(access_id),
  CONSTRAINT processed_documents_company_fkey FOREIGN KEY (company) REFERENCES public.companies(company_id)
);
CREATE TABLE public.processing_batches (
  batch_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  request_id text NOT NULL UNIQUE,
  total_documents integer NOT NULL,
  processed_documents integer DEFAULT 0,
  failed_documents integer DEFAULT 0,
  threshold_pct integer DEFAULT 60,
  save_to_training boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone,
  status text DEFAULT 'processing'::text,
  CONSTRAINT processing_batches_pkey PRIMARY KEY (batch_id)
);
CREATE TABLE public.raw_documents (
  document_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  document_name text NOT NULL,
  document_type text NOT NULL,
  link text NOT NULL,
  uploaded_by bigint,
  upload_date timestamp with time zone DEFAULT now(),
  file_size bigint,
  file_hash text,
  status text DEFAULT 'uploaded'::text,
  CONSTRAINT raw_documents_pkey PRIMARY KEY (document_id),
  CONSTRAINT raw_documents_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.access_control(access_id)
);
CREATE TABLE public.user_preferences (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  theme text DEFAULT 'light'::text CHECK (theme = ANY (ARRAY['light'::text, 'dark'::text])),
  language text DEFAULT 'en'::text,
  notifications_enabled boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_preferences_pkey PRIMARY KEY (id),
  CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.user_sessions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  session_token text NOT NULL UNIQUE,
  expires_at timestamp with time zone NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  last_accessed timestamp with time zone DEFAULT now(),
  CONSTRAINT user_sessions_pkey PRIMARY KEY (id),
  CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.users (
  id uuid NOT NULL,
  email text NOT NULL UNIQUE,
  full_name text,
  avatar_url text,
  role text DEFAULT 'user'::text CHECK (role = ANY (ARRAY['user'::text, 'admin'::text])),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id),
  CONSTRAINT users_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);