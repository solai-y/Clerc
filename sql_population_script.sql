-- SQL Population Script for Clerc Document Management System
-- This script populates the database with dummy data matching the current frontend structure
-- Run this after executing sql_creation_script.sql

-- Clear existing data (optional - uncomment if needed)
-- TRUNCATE TABLE document_access_logs, logs, processed_documents, raw_documents, categories, model_versions, companies, access_control RESTART IDENTITY CASCADE;

-- 1. Insert Access Control Users
INSERT INTO access_control ("user", api_key) VALUES
('admin', 'admin_api_key_12345'),
('john_doe', 'user_api_key_67890'),
('jane_smith', 'user_api_key_11111'),
('mike_wilson', 'user_api_key_22222'),
('sarah_johnson', 'user_api_key_33333');

-- 2. Insert Companies
INSERT INTO companies (company_name) VALUES
('Nomura Holdings'),
('JP Morgan Chase'),
('Goldman Sachs'),
('Morgan Stanley'),
('Credit Suisse'),
('Deutsche Bank'),
('HSBC'),
('Barclays'),
('UBS'),
('Citigroup');

-- 3. Insert Model Versions
INSERT INTO model_versions (model_name, version, description, deployed_date, parameters, metrics) VALUES
('DocumentClassifier', '1.0.0', 'Initial document classification model', '2024-01-01', '{"hidden_layers": 3, "learning_rate": 0.001}', '{"accuracy": 0.92, "f1_score": 0.89}'),
('TagExtractor', '2.1.0', 'Enhanced tag extraction model', '2024-01-15', '{"transformer_layers": 12, "attention_heads": 8}', '{"precision": 0.94, "recall": 0.87}'),
('CategoryPredictor', '1.5.2', 'Hierarchical category prediction model', '2024-02-01', '{"ensemble_models": 5, "voting": "soft"}', '{"macro_f1": 0.91, "micro_f1": 0.93}');

-- 4. Insert Categories (hierarchical structure matching frontend tags/subtags)
INSERT INTO categories (category_name, description, parent_category_id) VALUES
-- Main Categories
('Financial Report', 'Financial reporting documents', NULL),
('Risk Management', 'Risk assessment and management documents', NULL),
('Investment', 'Investment related documents', NULL),
('Market Analysis', 'Market research and analysis documents', NULL),
('Compliance', 'Regulatory compliance documents', NULL),
('Strategy', 'Strategic planning documents', NULL),
('Portfolio', 'Portfolio management documents', NULL),
('Quarterly', 'Quarterly reporting documents', NULL),
('Annual', 'Annual reporting documents', NULL),
('Assessment', 'Various assessment documents', NULL),
('Data', 'Data and analytics documents', NULL),
('Trends', 'Trend analysis documents', NULL),
('Regulatory', 'Regulatory documents', NULL),
('Checklist', 'Checklist and procedure documents', NULL),
('Research', 'Research documents', NULL),
('Audit', 'Audit related documents', NULL),
('Operations', 'Operational documents', NULL),
('Trading', 'Trading related documents', NULL),
('Client', 'Client related documents', NULL),
('Internal', 'Internal company documents', NULL);

-- Sub-categories (referencing parent categories)
INSERT INTO categories (category_name, description, parent_category_id) VALUES
-- Financial Report subcategories
('Income Statement', 'Income statement documents', 1),
('Balance Sheet', 'Balance sheet documents', 1),
('Cash Flow', 'Cash flow statement documents', 1),
('Profit & Loss', 'P&L statements', 1),
-- Risk Management subcategories
('Credit Risk', 'Credit risk assessment', 2),
('Market Risk', 'Market risk analysis', 2),
('Operational Risk', 'Operational risk documents', 2),
('Liquidity Risk', 'Liquidity risk assessment', 2),
-- Investment subcategories
('Equity Investment', 'Equity investment documents', 3),
('Bond Investment', 'Bond investment documents', 3),
('Alternative Investment', 'Alternative investment strategies', 3),
('Fixed Income', 'Fixed income investments', 3),
-- Market Analysis subcategories
('Technical Analysis', 'Technical market analysis', 4),
('Fundamental Analysis', 'Fundamental market analysis', 4),
('Market Trends', 'Market trend analysis', 4),
('Industry Trends', 'Industry specific trends', 4),
-- Compliance subcategories
('SOX Compliance', 'Sarbanes-Oxley compliance', 5),
('Basel III', 'Basel III regulatory compliance', 5),
('SEC Requirements', 'SEC regulatory requirements', 5),
('FINRA Rules', 'FINRA regulatory rules', 5),
('Regulatory Compliance', 'General regulatory compliance', 5),
('Internal Compliance', 'Internal compliance procedures', 5),
-- Strategy subcategories
('Business Strategy', 'Business strategy documents', 6),
('Investment Strategy', 'Investment strategy planning', 6),
('Long-term Strategy', 'Long-term strategic planning', 6),
('Short-term Strategy', 'Short-term strategic planning', 6),
-- Portfolio subcategories
('Portfolio Analysis', 'Portfolio performance analysis', 7),
('Asset Allocation', 'Asset allocation strategies', 7),
('Diversified Portfolio', 'Diversified portfolio management', 7),
('Portfolio Optimization', 'Portfolio optimization techniques', 7),
-- Quarterly subcategories
('Q1 2024', 'Q1 2024 reports', 8),
('Q2 2024', 'Q2 2024 reports', 8),
('Q3 2024', 'Q3 2024 reports', 8),
('Q4 2024', 'Q4 2024 reports', 8),
-- Data subcategories
('Historical Data', 'Historical data analysis', 11),
('Real-time Data', 'Real-time data processing', 11),
('Market Data', 'Market data analysis', 11),
-- Assessment subcategories
('Annual Assessment', 'Annual assessments', 10),
('Monthly Assessment', 'Monthly assessments', 10),
('Risk Assessment', 'Risk assessments', 10),
-- Checklist subcategories
('Monthly Checklist', 'Monthly procedure checklists', 14),
('Annual Checklist', 'Annual procedure checklists', 14),
('Audit Checklist', 'Audit procedure checklists', 14);

-- 5. Insert Raw Documents (50+ entries with realistic financial document names)
INSERT INTO raw_documents (document_name, document_type, link, categories, uploaded_by, company, upload_date) VALUES
('Q3_Financial_Report.pdf', 'PDF', 'https://storage.supabase.co/documents/Q3_Financial_Report.pdf', ARRAY[1, 8, 47], 1, 1, '2024-01-15'),
('Risk_Assessment_2024.docx', 'DOCX', 'https://storage.supabase.co/documents/Risk_Assessment_2024.docx', ARRAY[2, 10, 5], 2, 1, '2024-01-14'),
('Investment_Strategy.pdf', 'PDF', 'https://storage.supabase.co/documents/Investment_Strategy.pdf', ARRAY[3, 6, 7], 3, 1, '2024-01-13'),
('Market_Analysis_Jan.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Market_Analysis_Jan.xlsx', ARRAY[4, 11, 12], 4, 1, '2024-01-12'),
('Compliance_Checklist.pdf', 'PDF', 'https://storage.supabase.co/documents/Compliance_Checklist.pdf', ARRAY[5, 13, 14], 5, 1, '2024-01-11'),
('Annual_Report_2023.pdf', 'PDF', 'https://storage.supabase.co/documents/Annual_Report_2023.pdf', ARRAY[1, 9], 1, 1, '2024-01-10'),
('Credit_Risk_Analysis.docx', 'DOCX', 'https://storage.supabase.co/documents/Credit_Risk_Analysis.docx', ARRAY[2, 25], 2, 1, '2024-01-09'),
('Portfolio_Performance_Q4.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Portfolio_Performance_Q4.xlsx', ARRAY[7, 43, 48], 3, 1, '2024-01-08'),
('SEC_Filing_Form_10K.pdf', 'PDF', 'https://storage.supabase.co/documents/SEC_Filing_Form_10K.pdf', ARRAY[5, 37], 4, 1, '2024-01-07'),
('Trading_Strategy_Bonds.pdf', 'PDF', 'https://storage.supabase.co/documents/Trading_Strategy_Bonds.pdf', ARRAY[3, 30, 18], 5, 1, '2024-01-06'),
('Market_Volatility_Report.docx', 'DOCX', 'https://storage.supabase.co/documents/Market_Volatility_Report.docx', ARRAY[4, 26, 33], 1, 2, '2024-01-05'),
('Internal_Audit_Findings.pdf', 'PDF', 'https://storage.supabase.co/documents/Internal_Audit_Findings.pdf', ARRAY[16, 20, 36], 2, 2, '2024-01-04'),
('Equity_Research_Tech.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Equity_Research_Tech.xlsx', ARRAY[3, 29, 15], 3, 2, '2024-01-03'),
('Liquidity_Risk_Assessment.docx', 'DOCX', 'https://storage.supabase.co/documents/Liquidity_Risk_Assessment.docx', ARRAY[2, 28], 4, 2, '2024-01-02'),
('Client_Portfolio_Review.pdf', 'PDF', 'https://storage.supabase.co/documents/Client_Portfolio_Review.pdf', ARRAY[7, 19, 43], 5, 2, '2024-01-01'),
('Operational_Procedures.docx', 'DOCX', 'https://storage.supabase.co/documents/Operational_Procedures.docx', ARRAY[17, 27], 1, 3, '2023-12-31'),
('Fixed_Income_Strategy.pdf', 'PDF', 'https://storage.supabase.co/documents/Fixed_Income_Strategy.pdf', ARRAY[3, 32, 6], 2, 3, '2023-12-30'),
('Basel_III_Implementation.docx', 'DOCX', 'https://storage.supabase.co/documents/Basel_III_Implementation.docx', ARRAY[5, 35], 3, 3, '2023-12-29'),
('Monthly_Trading_Report.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Monthly_Trading_Report.xlsx', ARRAY[18, 52], 4, 3, '2023-12-28'),
('Alternative_Investment_Analysis.pdf', 'PDF', 'https://storage.supabase.co/documents/Alternative_Investment_Analysis.pdf', ARRAY[3, 31], 5, 3, '2023-12-27'),
('Cash_Flow_Projection.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Cash_Flow_Projection.xlsx', ARRAY[1, 23], 1, 4, '2023-12-26'),
('FINRA_Compliance_Update.pdf', 'PDF', 'https://storage.supabase.co/documents/FINRA_Compliance_Update.pdf', ARRAY[5, 38], 2, 4, '2023-12-25'),
('Technical_Analysis_Report.docx', 'DOCX', 'https://storage.supabase.co/documents/Technical_Analysis_Report.docx', ARRAY[4, 33], 3, 4, '2023-12-24'),
('Asset_Allocation_Model.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Asset_Allocation_Model.xlsx', ARRAY[7, 44], 4, 4, '2023-12-23'),
('Business_Continuity_Plan.pdf', 'PDF', 'https://storage.supabase.co/documents/Business_Continuity_Plan.pdf', ARRAY[17, 40], 5, 4, '2023-12-22'),
('Q2_Earnings_Call_Transcript.pdf', 'PDF', 'https://storage.supabase.co/documents/Q2_Earnings_Call_Transcript.pdf', ARRAY[1, 8, 46], 1, 5, '2023-12-21'),
('Derivative_Trading_Policy.docx', 'DOCX', 'https://storage.supabase.co/documents/Derivative_Trading_Policy.docx', ARRAY[18, 5], 2, 5, '2023-12-20'),
('ESG_Investment_Guidelines.pdf', 'PDF', 'https://storage.supabase.co/documents/ESG_Investment_Guidelines.pdf', ARRAY[3, 40], 3, 5, '2023-12-19'),
('Market_Risk_Metrics.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Market_Risk_Metrics.xlsx', ARRAY[2, 26, 11], 4, 5, '2023-12-18'),
('Fund_Performance_Analysis.pdf', 'PDF', 'https://storage.supabase.co/documents/Fund_Performance_Analysis.pdf', ARRAY[7, 43, 15], 5, 5, '2023-12-17'),
('Regulatory_Change_Impact.docx', 'DOCX', 'https://storage.supabase.co/documents/Regulatory_Change_Impact.docx', ARRAY[5, 13], 1, 6, '2023-12-16'),
('Investment_Committee_Minutes.pdf', 'PDF', 'https://storage.supabase.co/documents/Investment_Committee_Minutes.pdf', ARRAY[3, 20], 2, 6, '2023-12-15'),
('Stress_Test_Results.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Stress_Test_Results.xlsx', ARRAY[2, 10], 3, 6, '2023-12-14'),
('Client_Onboarding_Checklist.pdf', 'PDF', 'https://storage.supabase.co/documents/Client_Onboarding_Checklist.pdf', ARRAY[19, 14, 57], 4, 6, '2023-12-13'),
('Currency_Hedging_Strategy.docx', 'DOCX', 'https://storage.supabase.co/documents/Currency_Hedging_Strategy.docx', ARRAY[3, 6, 18], 5, 6, '2023-12-12'),
('Audit_Trail_Report.pdf', 'PDF', 'https://storage.supabase.co/documents/Audit_Trail_Report.pdf', ARRAY[16, 20], 1, 7, '2023-12-11'),
('Economic_Outlook_2024.docx', 'DOCX', 'https://storage.supabase.co/documents/Economic_Outlook_2024.docx', ARRAY[4, 15, 34], 2, 7, '2023-12-10'),
('Portfolio_Rebalancing_Guide.pdf', 'PDF', 'https://storage.supabase.co/documents/Portfolio_Rebalancing_Guide.pdf', ARRAY[7, 45], 3, 7, '2023-12-09'),
('KYC_Documentation.docx', 'DOCX', 'https://storage.supabase.co/documents/KYC_Documentation.docx', ARRAY[19, 5], 4, 7, '2023-12-08'),
('Interest_Rate_Analysis.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Interest_Rate_Analysis.xlsx', ARRAY[4, 32], 5, 7, '2023-12-07'),
('Trading_Limit_Policies.pdf', 'PDF', 'https://storage.supabase.co/documents/Trading_Limit_Policies.pdf', ARRAY[18, 5], 1, 8, '2023-12-06'),
('Investment_Risk_Disclosure.docx', 'DOCX', 'https://storage.supabase.co/documents/Investment_Risk_Disclosure.docx', ARRAY[3, 2, 19], 2, 8, '2023-12-05'),
('Monthly_P&L_Statement.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Monthly_P&L_Statement.xlsx', ARRAY[1, 24], 3, 8, '2023-12-04'),
('Cybersecurity_Assessment.pdf', 'PDF', 'https://storage.supabase.co/documents/Cybersecurity_Assessment.pdf', ARRAY[17, 10], 4, 8, '2023-12-03'),
('Bond_Portfolio_Analysis.docx', 'DOCX', 'https://storage.supabase.co/documents/Bond_Portfolio_Analysis.docx', ARRAY[7, 30, 43], 5, 8, '2023-12-02'),
('Commodity_Trading_Report.pdf', 'PDF', 'https://storage.supabase.co/documents/Commodity_Trading_Report.pdf', ARRAY[18, 4], 1, 9, '2023-12-01'),
('Due_Diligence_Report.docx', 'DOCX', 'https://storage.supabase.co/documents/Due_Diligence_Report.docx', ARRAY[15, 3], 2, 9, '2023-11-30'),
('Liquidity_Coverage_Ratio.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Liquidity_Coverage_Ratio.xlsx', ARRAY[2, 28, 5], 3, 9, '2023-11-29'),
('Client_Investment_Profile.pdf', 'PDF', 'https://storage.supabase.co/documents/Client_Investment_Profile.pdf', ARRAY[19, 3], 4, 9, '2023-11-28'),
('Market_Making_Guidelines.docx', 'DOCX', 'https://storage.supabase.co/documents/Market_Making_Guidelines.docx', ARRAY[18, 17], 5, 9, '2023-11-27'),
('Quarterly_Risk_Report.pdf', 'PDF', 'https://storage.supabase.co/documents/Quarterly_Risk_Report.pdf', ARRAY[2, 8, 49], 1, 10, '2023-11-26'),
('Structured_Product_Analysis.xlsx', 'XLSX', 'https://storage.supabase.co/documents/Structured_Product_Analysis.xlsx', ARRAY[3, 15], 2, 10, '2023-11-25'),
('Compliance_Training_Materials.pdf', 'PDF', 'https://storage.supabase.co/documents/Compliance_Training_Materials.pdf', ARRAY[5, 20], 3, 10, '2023-11-24'),
('Foreign_Exchange_Policy.docx', 'DOCX', 'https://storage.supabase.co/documents/Foreign_Exchange_Policy.docx', ARRAY[18, 17], 4, 10, '2023-11-23'),
('Performance_Attribution_Report.pdf', 'PDF', 'https://storage.supabase.co/documents/Performance_Attribution_Report.pdf', ARRAY[7, 43], 5, 10, '2023-11-22');

-- 6. Insert Processed Documents (AI analysis results)
INSERT INTO processed_documents (document_id, model_id, explanation, important_keywords, confidence_score, verified, predicted_categories) VALUES
(1, 1, 'Financial report containing quarterly earnings and performance metrics', ARRAY['quarterly', 'financial', 'revenue', 'earnings', 'performance'], 0.92, true, ARRAY[1, 8, 21]),
(2, 2, 'Risk assessment document analyzing various risk factors', ARRAY['risk', 'assessment', 'compliance', 'credit', 'market'], 0.88, true, ARRAY[2, 25, 5]),
(3, 1, 'Investment strategy document outlining portfolio approaches', ARRAY['investment', 'strategy', 'portfolio', 'equity', 'diversification'], 0.91, true, ARRAY[3, 6, 7]),
(4, 2, 'Market analysis spreadsheet with technical indicators', ARRAY['market', 'analysis', 'trends', 'technical', 'data'], 0.85, true, ARRAY[4, 33, 11]),
(5, 1, 'Compliance checklist for regulatory requirements', ARRAY['compliance', 'regulatory', 'checklist', 'sox', 'basel'], 0.94, true, ARRAY[5, 14, 35]),
(6, 1, 'Annual comprehensive financial report', ARRAY['annual', 'financial', 'comprehensive', 'performance'], 0.89, true, ARRAY[1, 9]),
(7, 2, 'Credit risk analysis with detailed metrics', ARRAY['credit', 'risk', 'analysis', 'metrics', 'exposure'], 0.93, true, ARRAY[2, 25]),
(8, 1, 'Portfolio performance review for Q4', ARRAY['portfolio', 'performance', 'quarterly', 'review'], 0.87, true, ARRAY[7, 43, 48]),
(9, 2, 'SEC regulatory filing document', ARRAY['sec', 'filing', 'regulatory', 'compliance'], 0.96, true, ARRAY[5, 37]),
(10, 1, 'Bond trading strategy document', ARRAY['trading', 'bonds', 'strategy', 'fixed income'], 0.84, true, ARRAY[18, 30, 3]);

-- 7. Insert Logs (Audit trail)
INSERT INTO logs (action_type, document_id, access_id, action_details) VALUES
('UPLOAD', 1, 1, '{"file_size": "2.4MB", "upload_method": "web_interface"}'),
('CLASSIFY', 1, 1, '{"model_used": "DocumentClassifier_v1.0.0", "confidence": 0.92}'),
('VIEW', 1, 2, '{"view_duration": "5m 23s", "page_views": 12}'),
('DOWNLOAD', 1, 2, '{"download_format": "PDF", "file_size": "2.4MB"}'),
('EDIT_TAGS', 1, 1, '{"old_tags": ["Financial Report"], "new_tags": ["Financial Report", "Quarterly", "Revenue"]}'),
('UPLOAD', 2, 2, '{"file_size": "1.8MB", "upload_method": "api"}'),
('CLASSIFY', 2, 2, '{"model_used": "DocumentClassifier_v1.0.0", "confidence": 0.88}'),
('VIEW', 2, 3, '{"view_duration": "3m 45s", "page_views": 8}'),
('UPLOAD', 3, 3, '{"file_size": "3.1MB", "upload_method": "web_interface"}'),
('CLASSIFY', 3, 3, '{"model_used": "DocumentClassifier_v1.0.0", "confidence": 0.91}');

-- 8. Insert Document Access Logs
INSERT INTO document_access_logs (document_id, access_type, ip_address, user_agent, success) VALUES
(1, 'VIEW', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', true),
(1, 'DOWNLOAD', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', true),
(2, 'VIEW', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', true),
(3, 'VIEW', '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', true),
(4, 'VIEW', '192.168.1.103', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15', true),
(5, 'VIEW', '192.168.1.104', 'Mozilla/5.0 (Android 11; Mobile; rv:89.0) Gecko/89.0 Firefox/89.0', true);

-- Create indexes for better performance
CREATE INDEX idx_raw_documents_company ON raw_documents(company);
CREATE INDEX idx_raw_documents_upload_date ON raw_documents(upload_date);
CREATE INDEX idx_raw_documents_categories ON raw_documents USING GIN(categories);
CREATE INDEX idx_processed_documents_confidence ON processed_documents(confidence_score);
CREATE INDEX idx_logs_action_date ON logs(action_date);
CREATE INDEX idx_categories_parent ON categories(parent_category_id);

-- Update statistics
ANALYZE;

-- Summary: 
-- - 5 users in access_control
-- - 10 companies
-- - 3 model versions
-- - 57 categories (20 main + 37 sub-categories)
-- - 54 raw documents with realistic financial names
-- - 10 processed documents with AI analysis
-- - 10 audit log entries
-- - 6 document access log entries
-- - Performance indexes created