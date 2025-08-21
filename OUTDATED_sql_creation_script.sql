-- 1. Access Control
create table access_control (
  access_id bigint primary key generated always as identity,
  "user" text not null,
  api_key text not null
);

-- 2. Companies
create table companies (
  company_id bigint primary key generated always as identity,
  company_name text not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- 3. Model Versions
create table model_versions (
  model_id bigint primary key generated always as identity,
  model_name text not null,
  version text not null,
  description text,
  deployed_date timestamp with time zone,
  parameters jsonb,
  metrics jsonb
);

-- 4. Categories (supports hierarchical structure)
create table categories (
  category_id bigint primary key generated always as identity,
  category_name text not null,
  description text,
  parent_category_id bigint references categories(category_id),
  created_at timestamp with time zone default now()
);

-- 5. Raw Documents
create table raw_documents (
  document_id bigint primary key generated always as identity,
  document_name text not null,
  document_type text not null,
  link text not null,
  categories bigint[] default '{}',
  uploaded_by bigint references access_control(access_id) on delete set null,
  company bigint references companies(company_id) on delete set null,
  upload_date timestamp with time zone default now()
);

-- 6. Processed Documents
create table processed_documents (
  process_id bigint primary key generated always as identity,
  document_id bigint references raw_documents(document_id) on delete cascade,
  model_id bigint references model_versions(model_id) on delete set null,
  explanation text,
  important_keywords text[],
  confidence_score float,
  verified boolean,
  classification_date timestamp with time zone default now(),
  predicted_categories bigint[]
);

-- 7. Logs (Audit trail)
create table logs (
  log_id bigint primary key generated always as identity,
  action_type text not null,
  action_date timestamp with time zone default now(),
  document_id bigint references raw_documents(document_id) on delete set null,
  access_id bigint references access_control(access_id) on delete set null,
  action_details jsonb
);

-- 8. Document Access Logs
create table document_access_logs (
  access_id bigint primary key generated always as identity,
  document_id bigint references raw_documents(document_id) on delete cascade,
  access_date timestamp with time zone default now(),
  access_type text,
  ip_address text,
  user_agent text,
  success boolean
);
