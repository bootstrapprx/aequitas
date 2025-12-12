-- Migration: Add pgvector extension and embedding columns
-- Date: 2025-12-11
-- Description: Enables pgvector extension and adds embedding fields to support semantic search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to master_accounts
-- 384 dimensions for all-MiniLM-L6-v2 model
ALTER TABLE master_accounts
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Add embedding column to company_accounts
ALTER TABLE company_accounts
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Create indexes for vector similarity search
-- Using ivfflat index for fast approximate nearest neighbor search
-- Lists parameter: sqrt(row_count) is a good starting point
CREATE INDEX IF NOT EXISTS master_accounts_embedding_idx
ON master_accounts USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS company_accounts_embedding_idx
ON company_accounts USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Note: After adding embeddings to existing rows, you should run:
-- REINDEX INDEX master_accounts_embedding_idx;
-- REINDEX INDEX company_accounts_embedding_idx;

-- Example query for semantic search (for reference):
-- SELECT code, description, 1 - (embedding <=> '[0.1, 0.2, ...]') AS similarity
-- FROM master_accounts
-- WHERE embedding IS NOT NULL
-- ORDER BY embedding <=> '[0.1, 0.2, ...]'
-- LIMIT 10;
