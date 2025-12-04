-- Migration: Create system_settings table
-- This table stores global application settings

BEGIN;

CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    maintenance_mode BOOLEAN NOT NULL DEFAULT FALSE,
    allow_public_signup BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings if table is empty
INSERT INTO system_settings (id, maintenance_mode, allow_public_signup)
SELECT 1, FALSE, FALSE
WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE id = 1);

COMMIT;
