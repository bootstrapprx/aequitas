-- Migration: Add Enriched Fields to Master Accounts
-- Date: 2025-12-01
-- Description: Adds AI-ready fields for DEXTER integration and IFRS/GAAP compliance

-- Add new columns to master_accounts table
ALTER TABLE master_accounts 
ADD COLUMN IF NOT EXISTS long_description TEXT,
ADD COLUMN IF NOT EXISTS fs_mapping VARCHAR(50),
ADD COLUMN IF NOT EXISTS tags TEXT[],
ADD COLUMN IF NOT EXISTS default_vendors TEXT[],
ADD COLUMN IF NOT EXISTS regulatory_mapping JSONB,
ADD COLUMN IF NOT EXISTS normal_balance VARCHAR(20),
ADD COLUMN IF NOT EXISTS cash_flow_classification VARCHAR(50),
ADD COLUMN IF NOT EXISTS cost_center VARCHAR(50);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_master_accounts_category ON master_accounts(category);
CREATE INDEX IF NOT EXISTS idx_master_accounts_fs_mapping ON master_accounts(fs_mapping);
CREATE INDEX IF NOT EXISTS idx_master_accounts_normal_balance ON master_accounts(normal_balance);
CREATE INDEX IF NOT EXISTS idx_master_accounts_tags ON master_accounts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_master_accounts_default_vendors ON master_accounts USING GIN(default_vendors);

-- Add comments for documentation
COMMENT ON COLUMN master_accounts.long_description IS 'Professional IFRS/GAAP explanation of the account';
COMMENT ON COLUMN master_accounts.fs_mapping IS 'Financial statement mapping: Balance Sheet or Income Statement';
COMMENT ON COLUMN master_accounts.tags IS 'AI-friendly keywords for intelligent classification';
COMMENT ON COLUMN master_accounts.default_vendors IS 'Common vendor associations for automatic suggestion';
COMMENT ON COLUMN master_accounts.regulatory_mapping IS 'IFRS/IPSAS/ASC standard references';
COMMENT ON COLUMN master_accounts.normal_balance IS 'Normal balance type: Debit or Credit';
COMMENT ON COLUMN master_accounts.cash_flow_classification IS 'Cash flow statement classification';
COMMENT ON COLUMN master_accounts.cost_center IS 'Default cost center assignment';

-- Verification query
-- SELECT 
--     column_name, 
--     data_type, 
--     is_nullable,
--     column_default
-- FROM information_schema.columns 
-- WHERE table_name = 'master_accounts'
-- ORDER BY ordinal_position;
