# ICD-10 Data Population Guide

This guide explains how to populate the ICD-10 database with CMS data, embeddings, and AI-generated facets.

## Overview

The data population process consists of 4 steps:

1. **Download** - Download official ICD-10-CM data from CMS
2. **Load** - Parse and load codes into database
3. **Embeddings** - Generate MedCPT embeddings for semantic search
4. **Facets** - Generate AI facets for clinical reasoning

## Prerequisites

1. **Database Setup**
   - PostgreSQL 15+ with pgvector extension installed
   - Database migrations applied (`alembic upgrade head`)
   - Database connection configured in `DATABASE_URL` environment variable

2. **Python Dependencies**
   - All requirements installed: `pip install -r requirements.txt`
   - Includes: sentence-transformers, torch, pgvector, etc.

3. **Hardware Requirements**
   - Embeddings: GPU recommended but not required (CPU works, just slower)
   - Disk space: ~500MB for data files, ~1GB for embeddings
   - RAM: 4GB minimum (8GB recommended for embedding generation)

## Step-by-Step Instructions

### Step 1: Download CMS ICD-10-CM Data

Download the official ICD-10-CM code files from CMS:

```bash
# Download 2024 data (default)
python scripts/download_icd10_data.py

# Download specific year
python scripts/download_icd10_data.py --year 2024

# List downloaded files
python scripts/download_icd10_data.py --list
```

**What this does:**
- Downloads ICD-10-CM codes, descriptions, and guidelines from CMS
- Extracts zip files to `data/icd10/{year}/` directory
- Typically downloads ~72,000 ICD-10-CM codes

**Troubleshooting:**
- If download fails, check CMS website for updated URLs (URLs change annually)
- Update URLs in `download_icd10_data.py` script if needed
- CMS data source: https://www.cms.gov/medicare/coding-billing/icd-10-codes

### Step 2: Load Codes into Database

Parse the downloaded files and load codes into the database:

```bash
# Load codes (uses DATABASE_URL from environment)
python scripts/load_icd10_data.py

# Specify database URL
python scripts/load_icd10_data.py --db-url "postgresql://user:pass@localhost:5432/dbname"

# Load specific year
python scripts/load_icd10_data.py --year 2024

# Dry run (parse but don't write to database)
python scripts/load_icd10_data.py --dry-run
```

**What this does:**
- Parses ICD-10-CM text files
- Loads codes, descriptions, chapters, and categories
- Creates parent-child relationships between codes
- Handles code updates (existing codes are updated, new ones added)

**Output:**
- Progress: Shows batch progress (commits every 1000 codes)
- Summary: Number of codes added/updated and relationships created
- Expected: ~72,000 codes loaded, ~100,000+ relationships created

**Troubleshooting:**
- Ensure database migrations are applied first
- Check DATABASE_URL connection string
- For parsing errors, try `--dry-run` to see sample output

### Step 3: Generate Embeddings

Generate MedCPT embeddings for semantic search:

```bash
# Generate embeddings with default settings
python scripts/generate_embeddings.py

# Specify batch size (larger = faster but more memory)
python scripts/generate_embeddings.py --batch-size 64

# Force regenerate all embeddings
python scripts/generate_embeddings.py --force

# Verify embeddings only (don't generate)
python scripts/generate_embeddings.py --verify-only

# Show sample embeddings after generation
python scripts/generate_embeddings.py --sample
```

**What this does:**
- Generates 768-dimensional embeddings using MedCPT model
- Processes codes in batches for efficiency
- Skips codes that already have embeddings (unless `--force`)
- Shows progress bar with estimated time

**Performance:**
- CPU: ~10-20 codes/second (~1-2 hours for 72k codes)
- GPU: ~100-200 codes/second (~5-10 minutes for 72k codes)
- Memory: ~2GB for model + batch processing

**Model Details:**
- Primary model: `ncbi/MedCPT-Query-Encoder` (768-dim, biomedical)
- Fallback model: `all-MiniLM-L6-v2` (384-dim, general purpose)
- First run downloads model (~1GB), subsequent runs use cache

**Troubleshooting:**
- Out of memory: Reduce `--batch-size` (try 16 or 8)
- Model download fails: Check internet connection, model downloads from HuggingFace
- For CPU-only: Set `CUDA_VISIBLE_DEVICES=""` to force CPU mode

### Step 4: Generate AI Facets

Generate clinical facets for codes using rule-based classification:

```bash
# Generate facets with default settings
python scripts/populate_ai_facets.py

# Specify batch size
python scripts/populate_ai_facets.py --batch-size 200

# Force regenerate all facets
python scripts/populate_ai_facets.py --force

# Verify facets only
python scripts/populate_ai_facets.py --verify-only --sample

# Show sample facets
python scripts/populate_ai_facets.py --sample
```

**What this does:**
- Generates clinical metadata: body_system, concept_type, chronicity, severity, etc.
- Uses rule-based classification based on code structure and keywords
- Creates facets for filtering and clinical reasoning

**Facets Generated:**
- `body_system`: cardiovascular, respiratory, digestive, etc.
- `concept_type`: diagnosis, procedure, symptom, injury, screening
- `chronicity`: acute, chronic, subacute
- `severity`: mild, moderate, severe, life-threatening
- `acuity`: acute, chronic, subacute
- `laterality`: left, right, bilateral, unspecified
- `onset_context`: congenital, acquired, traumatic, iatrogenic
- `age_band`: neonatal, pediatric, adult, geriatric
- `sex_specific`: male, female, both
- `risk_flag`: boolean for high-risk conditions

**Performance:**
- ~500-1000 codes/second (very fast, rule-based)
- Total time: ~1-2 minutes for 72k codes

**Note on Production:**
The current implementation uses rule-based classification. For production use with higher accuracy, consider:
1. Integrating with LLM API (OpenAI, Claude, etc.)
2. Using fine-tuned models for medical classification
3. Manual review and curation of high-volume codes

## Complete Workflow Example

Here's a complete example of populating the database from scratch:

```bash
# 1. Ensure database is ready
export DATABASE_URL="postgresql://user:pass@localhost:5432/medcodeapi"
alembic upgrade head

# 2. Download data
python scripts/download_icd10_data.py --year 2024

# 3. Load codes
python scripts/load_icd10_data.py --year 2024

# 4. Generate embeddings (this takes the longest)
python scripts/generate_embeddings.py --batch-size 32

# 5. Generate facets
python scripts/populate_ai_facets.py

# 6. Verify everything
python scripts/generate_embeddings.py --verify-only
python scripts/populate_ai_facets.py --verify-only --sample
```

## Verification

After running all scripts, verify the data:

```sql
-- Check code counts
SELECT code_system, COUNT(*)
FROM icd10_codes
GROUP BY code_system;

-- Check embedding coverage
SELECT
  COUNT(*) as total_codes,
  COUNT(embedding) as codes_with_embeddings,
  ROUND(COUNT(embedding)::numeric / COUNT(*) * 100, 2) as coverage_percent
FROM icd10_codes
WHERE code_system = 'ICD10-CM';

-- Check facet coverage
SELECT
  (SELECT COUNT(*) FROM icd10_codes WHERE code_system = 'ICD10-CM') as total_codes,
  COUNT(*) as codes_with_facets,
  ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM icd10_codes WHERE code_system = 'ICD10-CM') * 100, 2) as coverage_percent
FROM icd10_ai_facets
WHERE code_system = 'ICD10-CM';

-- Check relationships
SELECT relation_type, COUNT(*)
FROM icd10_relations
GROUP BY relation_type;

-- Sample codes with all data
SELECT
  c.code,
  c.short_desc,
  c.chapter,
  f.body_system,
  f.concept_type,
  f.chronicity,
  CASE WHEN c.embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding
FROM icd10_codes c
LEFT JOIN icd10_ai_facets f ON c.code = f.code AND c.code_system = f.code_system
WHERE c.code_system = 'ICD10-CM'
LIMIT 10;
```

## Updating Data

To update codes with new annual releases:

```bash
# Download new year data
python scripts/download_icd10_data.py --year 2025

# Load new codes (existing codes will be updated)
python scripts/load_icd10_data.py --year 2025

# Generate embeddings for new codes only
python scripts/generate_embeddings.py

# Generate facets for new codes only
python scripts/populate_ai_facets.py
```

## Data Storage

Data is stored in the following locations:

- **Downloaded files**: `data/icd10/{year}/`
- **Database**: PostgreSQL tables
  - `icd10_codes` - Main codes table
  - `icd10_ai_facets` - Clinical facets
  - `icd10_relations` - Code relationships
  - `code_mappings` - Cross-system mappings (future)
  - `icd10_synonyms` - Alternative terms (future)

## Performance Tips

1. **Embeddings Generation**
   - Use GPU if available (10x faster)
   - Increase batch size for faster processing (if memory allows)
   - Run overnight for large datasets on CPU

2. **Database**
   - Ensure indexes are created (done by migration)
   - Use connection pooling for concurrent operations
   - Monitor disk space (embeddings add ~500MB)

3. **Memory Management**
   - Reduce batch size if running out of memory
   - Close other applications during embedding generation
   - For very large datasets, process in chunks

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check DATABASE_URL environment variable
   - Verify PostgreSQL is running
   - Test connection: `psql $DATABASE_URL`

2. **pgvector Extension Error**
   - Install pgvector: `CREATE EXTENSION vector;`
   - Verify: `SELECT * FROM pg_extension WHERE extname = 'vector';`

3. **Model Download Fails**
   - Check internet connection
   - Try manual download from HuggingFace
   - Use fallback model (automatically used on error)

4. **Out of Memory**
   - Reduce batch size: `--batch-size 8`
   - Close other applications
   - Use CPU instead of GPU for embeddings

5. **Parse Errors**
   - Try `--dry-run` to see what's being parsed
   - Check CMS file format (may change year to year)
   - Update parser in `load_icd10_data.py` if format changed

## Next Steps

After populating the data:

1. **Test Search Functions**
   - Try semantic search with test queries
   - Test faceted filtering
   - Verify hybrid search results

2. **Build API Endpoints**
   - Implement search endpoints using `icd10_search_service.py`
   - Add authentication/rate limiting
   - Deploy API

3. **Monitor Performance**
   - Check search latency (should be < 300ms for top-10)
   - Monitor index usage
   - Optimize queries if needed

4. **Enhance Facets** (Optional)
   - Integrate LLM for better classification
   - Add manual review workflow
   - Expand facet categories

## Support

For issues or questions:
- Check logs in console output
- Review database queries in verification section
- Check CMS website for updated data formats
- Review requirements.md for specification details
