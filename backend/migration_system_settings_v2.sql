-- Migration: Replace system_settings table for admin panel
-- This replaces the old key-value system_settings with a structured table

BEGIN;

-- Drop old table
DROP TABLE IF EXISTS system_settings;

-- Create new structured table
CREATE TABLE system_settings (
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
