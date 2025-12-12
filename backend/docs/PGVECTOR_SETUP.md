# pgvector Integration Guide

This document explains how to set up and use pgvector for semantic search in Aequitas.

## Overview

pgvector enables semantic similarity search for account mappings, allowing the system to find accounts that are conceptually similar even if they use different terminology.

**Example:**
- "Office Supplies" can match "Stationery Expense"
- "Vehicle Maintenance" can match "Auto Repair Costs"
- "Internet Service" can match "Telecommunications Expense"

## Architecture

### Components

1. **pgvector Extension** - PostgreSQL extension for vector similarity search
2. **sentence-transformers** - Python library for generating text embeddings
3. **Embedding Service** - Service layer for generating and managing embeddings
4. **Mapping Service** - Enhanced with semantic search capabilities
5. **API Endpoints** - REST endpoints for semantic search and blended suggestions

### Embedding Model

- **Model:** all-MiniLM-L6-v2
- **Dimensions:** 384
- **Size:** ~80MB
- **Speed:** ~3,000 sentences/second on CPU
- **Quality:** State-of-the-art for semantic similarity

## Setup Instructions

### 1. Enable pgvector Extension in PostgreSQL

```sql
-- Connect to your database
psql -U user -d aequitas_dev

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 2. Run Database Migration

```bash
cd backend

# Using Alembic (recommended for production)
alembic upgrade head

# Or run SQL directly (development)
psql -U user -d aequitas_dev -f alembic/versions/001_add_pgvector_extension.sql
```

This will:
- Enable pgvector extension
- Add `embedding` column to `master_accounts` table
- Add `embedding` column to `company_accounts` table
- Create vector indexes for fast similarity search

### 3. Install Python Dependencies

```bash
pip install pgvector==0.3.6
pip install sentence-transformers==3.3.1
```

Or if using Docker:
```bash
make rebuild
```

### 4. Generate Embeddings

Generate embeddings for all existing accounts:

```bash
cd backend

# Generate for both master chart and company accounts
python -m app.data.generate_embeddings

# Or generate for master chart only
python -m app.data.generate_embeddings --master-only

# Or generate for specific company
python -m app.data.generate_embeddings --company-id <uuid>
```

**Important:** After generating embeddings, reindex for optimal performance:

```sql
REINDEX INDEX master_accounts_embedding_idx;
REINDEX INDEX company_accounts_embedding_idx;
```

## Usage

### API Endpoints

#### 1. Semantic Search

Find semantically similar master accounts for a company account:

```bash
GET /api/v1/mappings/semantic-search/{company_account_id}?limit=5&min_similarity=0.5
```

**Response:**
```json
[
  {
    "code": "1.10.10",
    "description": "Office Supplies",
    "category": "Expenses",
    "similarity": 0.87
  },
  {
    "code": "1.10.11",
    "description": "Stationery",
    "category": "Expenses",
    "similarity": 0.82
  }
]
```

#### 2. Blended Suggestions (AI + Semantic)

Get mapping suggestions that blend AI and semantic search:

```bash
POST /api/v1/mappings/suggest-blended
  ?company_account_id=<uuid>
  &semantic_weight=0.3
  &auto_create=true
```

**Parameters:**
- `semantic_weight`: 0.0-1.0 (0.3 = 30% semantic, 70% AI)
- `auto_create`: Create mapping suggestion automatically

**Response:**
```json
{
  "company_account_id": "uuid",
  "company_account_name": "Office Stuff",
  "method": "blended",
  "suggestions": [
    {
      "account": {
        "code": "1.10.10",
        "description": "Office Supplies",
        "category": "Expenses"
      },
      "confidence": 0.91,
      "ai_confidence": 0.95,
      "semantic_similarity": 0.87,
      "reason": "Blended: AI=0.95, Semantic=0.87"
    }
  ],
  "top_match": { /* same structure */ }
}
```

### Service Layer Usage

```python
from app.services.mapping_service import MappingService
from app.db.session import get_db

db = next(get_db())
service = MappingService(db)

# Semantic search
results = service.find_similar_master_accounts(
    company_account_id=account_id,
    limit=5,
    min_similarity=0.5
)

# Blended suggestions
suggestions = service.suggest_mapping_with_embeddings(
    company_account_id=account_id,
    auto_create=True,
    use_semantic=True,
    semantic_weight=0.3
)
```

## Performance Considerations

### Index Tuning

The default ivfflat index uses `lists = 100`. Adjust based on your data size:

```sql
-- For smaller datasets (< 10,000 rows)
CREATE INDEX master_accounts_embedding_idx
ON master_accounts USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- For larger datasets (> 100,000 rows)
CREATE INDEX master_accounts_embedding_idx
ON master_accounts USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);

-- Rule of thumb: lists = sqrt(row_count)
```

### Embedding Generation

- **Batch processing:** Generate embeddings in batches of 50-100 for efficiency
- **Background jobs:** Use Celery or similar for large-scale generation
- **Incremental updates:** Only generate embeddings for new/modified accounts

### Query Performance

- **Cosine distance:** Fast, works well for normalized vectors
- **Limit results:** Keep `limit` parameter reasonable (5-20 results)
- **Similarity threshold:** Use `min_similarity` to filter poor matches

## Monitoring

### Check Embedding Coverage

```sql
-- Master chart coverage
SELECT
    COUNT(*) as total,
    COUNT(embedding) as with_embedding,
    ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as coverage_pct
FROM master_accounts;

-- Company accounts coverage
SELECT
    company_id,
    COUNT(*) as total,
    COUNT(embedding) as with_embedding,
    ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as coverage_pct
FROM company_accounts
GROUP BY company_id;
```

### Test Similarity Search

```sql
-- Find accounts similar to a specific account
WITH target AS (
    SELECT embedding FROM company_accounts WHERE id = '<uuid>'
)
SELECT
    code,
    description,
    1 - (embedding <=> (SELECT embedding FROM target)) AS similarity
FROM master_accounts
WHERE embedding IS NOT NULL
ORDER BY embedding <=> (SELECT embedding FROM target)
LIMIT 10;
```

## Troubleshooting

### Extension Not Found

```
ERROR: extension "vector" is not available
```

**Solution:** Install pgvector in PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt install postgresql-16-pgvector

# macOS (Homebrew)
brew install pgvector

# Docker
# Use postgres image with pgvector pre-installed
# Or install manually in container
```

### Embeddings Not Generated

**Check if service is available:**
```python
from app.services.embedding_service import is_embeddings_available
print(is_embeddings_available())  # Should return True
```

**Re-install dependencies:**
```bash
pip uninstall sentence-transformers
pip install sentence-transformers==3.3.1
```

### Poor Search Results

1. **Check embedding coverage** - Ensure both master and company accounts have embeddings
2. **Lower similarity threshold** - Try `min_similarity=0.4` instead of 0.5
3. **Adjust semantic weight** - Higher weight (0.5-0.7) favors semantic over AI
4. **Reindex** - Run `REINDEX INDEX` after bulk updates

## Production Deployment

### Environment Variables

```bash
# Optional: Specify custom embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Enable/disable semantic search
ENABLE_SEMANTIC_SEARCH=true
```

### Deployment Checklist

- [ ] Enable pgvector extension in production database
- [ ] Run Alembic migration: `alembic upgrade head`
- [ ] Install sentence-transformers: `pip install sentence-transformers`
- [ ] Generate embeddings for master chart: `python -m app.data.generate_embeddings --master-only`
- [ ] Generate embeddings for company accounts: `python -m app.data.generate_embeddings`
- [ ] Reindex vector indexes
- [ ] Test semantic search endpoint
- [ ] Monitor embedding coverage
- [ ] Set up periodic embedding updates (for new accounts)

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [sentence-transformers Documentation](https://www.sbert.net/)
- [all-MiniLM-L6-v2 Model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
