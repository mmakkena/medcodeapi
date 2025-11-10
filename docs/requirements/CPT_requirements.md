# 🧾 CPT & HCPCS Semantic Search & Mapping API — Requirements Document
**Project:** Nuvii.ai / CDI Agent — Medical Coding Intelligence Platform  
**Author:** Murali Makkena  
**Version:** 1.0  
**Date:** November 2025  

---

## 1  Purpose & Scope
This system manages and searches **CPT and HCPCS medical procedure codes** with semantic and keyword search, AMA-compliant text handling, and optional licensing integration.  
It provides:
- Unified CPT + HCPCS storage
- **Free paraphrased descriptors** (no license) and **official AMA descriptors** (licensed)
- **pgvector-based semantic retrieval**
- Optional cross-mapping to ICD-10 and SNOMED CT
- REST API endpoints for coding assistance and analytics

---

## 2  Functional Requirements

### 2.1 Core Features
1. Store CPT and HCPCS codes with paraphrased and official descriptions.  
2. Enable semantic + hybrid search.  
3. Maintain AMA license status per code.  
4. Allow future swap-in of licensed AMA data.  
5. Support cross-mapping to ICD-10 / SNOMED / LOINC.  
6. Provide REST API for search, lookup, and mappings.  

### 2.2 Non-Functional
| Attribute | Requirement |
|------------|-------------|
| **Database** | PostgreSQL ≥15 + `pgvector`, `pg_trgm` |
| **Vector Dimension** | 768 (using `uclnlp/MedCPT` model) |
| **Latency** | <300 ms for top-10 semantic matches |
| **Licensing** | AMA CPT license required for official text |
| **Security** | No PHI or patient data stored |
| **Compliance** | AMA copyright, CMS HCPCS public domain |

---

## 3  Data Model (PostgreSQL Schema)

### 3.1 `procedure_codes`
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE procedure_codes (
  code_id SERIAL PRIMARY KEY,
  code VARCHAR(10) NOT NULL,
  code_system VARCHAR(10) NOT NULL CHECK (code_system IN ('CPT','HCPCS')),
  paraphrased_desc TEXT,              -- ✅ Free paraphrased version
  short_desc TEXT,                    -- ⚖️ Official licensed descriptor
  category VARCHAR(50),               -- e.g., E/M, Surgery, Radiology
  is_active BOOLEAN DEFAULT TRUE,
  effective_date DATE,
  expiry_date DATE,
  version_year INT,
  license_status VARCHAR(20) DEFAULT 'free'
      CHECK (license_status IN ('free','AMA_licensed')),
  embedding VECTOR(768),              -- pgvector embedding for search
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX procedure_codes_embedding_ivf
ON procedure_codes USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX procedure_codes_text_gin
ON procedure_codes USING gin ((coalesce(paraphrased_desc,'') || ' ' || coalesce(short_desc,'')) gin_trgm_ops);
3.2 code_synonyms
sql
Copy code
CREATE TABLE code_synonyms (
  code VARCHAR(10) REFERENCES procedure_codes(code),
  synonym TEXT
);
3.3 code_mappings
sql
Copy code
CREATE TABLE code_mappings (
  id BIGSERIAL PRIMARY KEY,
  from_system VARCHAR(20) NOT NULL CHECK (from_system IN ('CPT','HCPCS')),
  from_code VARCHAR(20) NOT NULL,
  to_system VARCHAR(20) NOT NULL CHECK (to_system IN ('ICD10','ICD10-CM','ICD10-PCS','SNOMED','LOINC')),
  to_code VARCHAR(40) NOT NULL,
  map_type VARCHAR(30) NOT NULL CHECK (map_type IN ('exact','related','billing','clinical')),
  confidence NUMERIC(3,2),
  source_name VARCHAR(120),
  source_version VARCHAR(40),
  source_url TEXT,
  reviewed_by VARCHAR(120),
  effective_date DATE
);
4 Embedding Model Configuration
✅ Selected Model: uclnlp/MedCPT
Property	Value
Type	Biomedical contrastive embedding model
Dimension	768
License	MIT
Purpose	Optimized for CPT/ICD retrieval and medical concept similarity

Usage Pattern

Generate embeddings from paraphrased_desc (free text only).

Do not embed AMA-licensed text directly.

Update vector index periodically.

Example Python Script

python
Copy code
from sentence_transformers import SentenceTransformer
import psycopg2, json

model = SentenceTransformer("uclnlp/MedCPT")
texts = ["Established patient office visit – moderate complexity"]
vectors = model.encode(texts, normalize_embeddings=True)

cur.execute(
  "UPDATE procedure_codes SET embedding = %s WHERE code = %s",
  (json.dumps(vectors[0].tolist()), "99213")
)
5 API Specification
Base URL
bash
Copy code
/api/v1/procedure
GET /search
Search CPT/HCPCS codes by keyword or semantics.
Query Params

Name	Type	Description
q	string	Free-text query
limit	int	Default 10
semantic	bool	Use vector search

Response

json
Copy code
{
  "query": "office visit for established patient",
  "results": [
    {
      "code": "99213",
      "system": "CPT",
      "description": "Established patient office visit – moderate complexity",
      "license_status": "free",
      "similarity": 0.89
    }
  ]
}
GET /{code}
Retrieve metadata and descriptors.

json
Copy code
{
  "code": "99213",
  "system": "CPT",
  "paraphrased_desc": "Established patient office visit – moderate complexity",
  "short_desc": "Office or other outpatient visit for the evaluation and management of an established patient...",
  "category": "E/M",
  "license_status": "AMA_licensed",
  "version_year": 2025
}
GET /{code}/maps
Cross-system mappings (e.g., ICD-10).

json
Copy code
{
  "code": "99213",
  "maps": [
    {"to_system": "ICD10-CM", "to_code": "E11.9", "map_type": "clinical", "confidence": 0.82}
  ]
}
POST /semantic
Semantic vector search endpoint.
Body

json
Copy code
{"text": "routine follow-up visit for diabetes management"}
Returns similar codes ordered by cosine similarity.

6 Search Workflow
Load CPT and HCPCS master files.

Generate paraphrased descriptions for CPT codes (AI-generated or curated).

Embed only paraphrased text via MedCPT.

Build ANN index (ivfflat).

On query, embed user text → find nearest codes.

Return paraphrased results; include license_status for AMA text gating.

7 Compliance & Licensing
Data	Owner	License	Usage
CPT	AMA	Licensed	Use code numbers freely; text requires license
HCPCS Level II	CMS	Public domain	Full text allowed
Mappings (ICD/SNOMED)	Public or licensed	Follow respective licenses	

Compliance Rule:
If license_status='free', show paraphrased_desc;
If 'AMA_licensed', show short_desc.

Footer for UI/docs:

CPT® codes and descriptions © American Medical Association.
HCPCS Level II codes © Centers for Medicare & Medicaid Services.

8 Example SQL Queries
Semantic Search

sql
Copy code
SELECT code, paraphrased_desc,
       1 - (embedding <=> :query_vec) AS similarity
FROM procedure_codes
WHERE is_active = TRUE
ORDER BY embedding <=> :query_vec
LIMIT 10;
Cross-Map Lookup

sql
Copy code
SELECT to_system, to_code, map_type, confidence
FROM code_mappings
WHERE from_code='99213' AND from_system='CPT';
9 Example Unified Response
json
Copy code
{
  "query": "follow-up visit established diabetic patient",
  "matches": [
    {
      "code": "99213",
      "system": "CPT",
      "description": "Established patient office visit – moderate complexity",
      "similarity": 0.89,
      "license_status": "free",
      "crossmaps": [
        {"to_system": "ICD10-CM", "to_code": "E11.9", "map_type": "clinical", "confidence": 0.82}
      ]
    }
  ]
}
10 Deliverables
PostgreSQL DDL (tables + indexes)

Embedding generator (MedCPT)

REST API (FastAPI / Node / Go)

Loader for CPT & HCPCS datasets

Licensing configuration (AMA key or flag)

Unit tests for vector retrieval & compliance filtering

11 Future Enhancements
Integrate official AMA data pipeline once license obtained.

Fine-tune MedCPT on CPT note–code pairs for better recall.

Add HNSW index for real-time semantic queries.

Support CPT modifiers (-25, -59, etc.) and grouping.

Extend cross-maps to ICD-11, SNOMED, and HCPCS Level II G/J codes.

yaml
Copy code
