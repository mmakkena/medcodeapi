# 🧾 ICD-10 Semantic Search & Mapping API — Requirements Document
**Project:** Nuvii.ai / CDI Agent — Clinical Coding & AI Reasoning Platform  
**Author:** Murali Makkena  
**Version:** 1.0  
**Date:** November 2025  

---

## 1  Purpose & Scope
This system provides an **AI-ready ICD-10/ICD-10-CM/PCS database** that supports:
- Full-text and **semantic search** (pgvector + open-source embeddings)
- **Cross-mapping** to SNOMED CT, LOINC, CPT/HCPCS
- **AI reasoning metadata** (body system, chronicity, severity, etc.)
- A **REST API** for clinical coding assistants and analytics pipelines

---

## 2  Functional Requirements

### 2.1 Core Features
1. Store complete ICD-10 data with descriptors.  
2. Support semantic and hybrid (keyword + vector) search.  
3. Provide cross-maps to SNOMED, LOINC, CPT/HCPCS.  
4. Include reasoning facets (body system, acuity, laterality, etc.).  
5. Expose REST endpoints for search, retrieval, and filters.

### 2.2 Non-Functional 
| Attribute | Requirement |
|------------|--------------|
| **DB** | PostgreSQL ≥ 15 + `pgvector`, `pg_trgm` |
| **Vector Dim** | 768 (using MedCPT embeddings) |
| **Latency** | < 300 ms for top-10 semantic hits |
| **Scalability** | ≥ 100 k ICD codes + mappings |
| **Security** | No PHI stored in embeddings |
| **Licensing** | ICD/LOINC public domain; CPT IDs only |

---

## 3  Data Model (PostgreSQL)

### 3.1 `icd10_codes`
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE icd10_codes (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR(10) NOT NULL,
  code_system VARCHAR(15) NOT NULL CHECK (code_system IN ('ICD10','ICD10-CM','ICD10-PCS')),
  short_desc TEXT,
  long_desc  TEXT,
  chapter VARCHAR(120),
  block_range VARCHAR(20),
  category VARCHAR(120),
  is_active BOOLEAN DEFAULT TRUE,
  version_year INT,
  effective_date DATE,
  expiry_date DATE,
  embedding VECTOR(768),
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX icd10_codes_embedding_ivf
ON icd10_codes USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX icd10_codes_gin_trgm
ON icd10_codes USING gin ((coalesce(short_desc,'') || ' ' || coalesce(long_desc,'')) gin_trgm_ops);
3.2 icd10_ai_facets
sql
Copy code
CREATE TABLE icd10_ai_facets (
  code VARCHAR(10) NOT NULL,
  code_system VARCHAR(15) NOT NULL,
  concept_type VARCHAR(40),
  body_system VARCHAR(40),
  acuity VARCHAR(40),
  severity VARCHAR(40),
  chronicity VARCHAR(40),
  laterality VARCHAR(40),
  onset_context VARCHAR(40),
  age_band VARCHAR(40),
  sex_specific VARCHAR(10),
  risk_flag BOOLEAN,
  extra JSONB,
  PRIMARY KEY (code, code_system)
);
3.3 code_mappings
sql
Copy code
CREATE TABLE code_mappings (
  id BIGSERIAL PRIMARY KEY,
  from_system VARCHAR(20) NOT NULL,
  from_code VARCHAR(20) NOT NULL,
  to_system VARCHAR(20) NOT NULL,
  to_code VARCHAR(40) NOT NULL,
  map_type VARCHAR(30) NOT NULL,
  confidence NUMERIC(3,2),
  source_name VARCHAR(120),
  source_version VARCHAR(40),
  source_url TEXT,
  reviewed_by VARCHAR(120),
  review_note TEXT,
  effective_date DATE,
  expiry_date DATE
);
3.4 Relationships and Synonyms
sql
Copy code
CREATE TABLE icd10_relations (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR(10) NOT NULL,
  related_code VARCHAR(10) NOT NULL,
  relation_type VARCHAR(30)
);

CREATE TABLE icd10_synonyms (
  code VARCHAR(10) NOT NULL,
  synonym TEXT
);
4 Embedding Model Configuration
✅ Selected Model: uclnlp/MedCPT
Property	Value
Type	Biomedical contrastive embedding model
Dimension	768
License	MIT (open source)
Purpose	Optimized for ICD/CPT and clinical concept similarity

Why:

Trained on MIMIC-III and SNOMED/CPT pairs → excellent for diagnosis ↔ code retrieval

Open source, self-hostable (CPU or GPU)

Embeddings fit directly in pgvector 768-dim columns

Alternative Model
intfloat/e5-large-v2 (1024 dim, MIT) for general semantic retrieval.

Example Embedding Pipeline (Python)
python
Copy code
from sentence_transformers import SentenceTransformer
import psycopg2, json

model = SentenceTransformer("uclnlp/MedCPT")
texts = ["Type 2 diabetes mellitus without complications"]
vectors = model.encode(texts, normalize_embeddings=True)

conn = psycopg2.connect(dsn)
cur = conn.cursor()
cur.execute(
  "UPDATE icd10_codes SET embedding = %s WHERE code = %s",
  (json.dumps(vectors[0].tolist()), "E11.9")
)
conn.commit()
5 API Specification
Base URL
bash
Copy code
/api/v1/icd
Endpoints
GET /search
Param	Type	Description
q	string	Free-text query
limit	int	Results (default 10)
semantic	bool	Include vector search

Response

json
Copy code
{
  "query": "high blood sugar no complications",
  "results": [
    {
      "code": "E11.9",
      "system": "ICD10-CM",
      "short_desc": "Type 2 diabetes mellitus without complications",
      "similarity": 0.87
    }
  ]
}
GET /{code}
Retrieve full metadata.

json
Copy code
{
  "code": "E11.9",
  "system": "ICD10-CM",
  "short_desc": "Type 2 diabetes mellitus without complications",
  "long_desc": "Type 2 diabetes mellitus without complications",
  "chapter": "Endocrine, nutritional and metabolic diseases",
  "facets": {
    "concept_type": "diagnosis",
    "body_system": "endocrine",
    "chronicity": "chronic",
    "risk_flag": true
  }
}
GET /{code}/maps
Return cross-mapped codes.

json
Copy code
{
  "code": "E11.9",
  "maps": [
    {"to_system":"SNOMED","to_code":"44054006","map_type":"exact","confidence":0.95},
    {"to_system":"CPT","to_code":"36416","map_type":"billing","confidence":0.40}
  ]
}
POST /semantic
Perform embedding-based semantic retrieval.

json
Copy code
{ "text": "adult with long-standing diabetes and no acute symptoms" }
Response: same as /search with semantic scores.

GET /facets
Filter by reasoning metadata.
Query params → body_system, chronicity, age_band, etc.
Returns array of matching codes.

6 Embedding & Search Workflow
Load official ICD datasets (WHO/CDC).

Clean and normalize descriptions.

Generate 768-dim MedCPT embeddings.

Insert into icd10_codes.embedding.

Query using cosine similarity or hybrid keyword + vector ranking.
8 Example SQL Queries

Semantic Search

SELECT code, short_desc,
       1 - (embedding <=> :query_vec) AS similarity
FROM icd10_codes
ORDER BY embedding <=> :query_vec
LIMIT 10;


Facet Filter

SELECT i.code, i.short_desc
FROM icd10_codes i
JOIN icd10_ai_facets f USING (code, code_system)
WHERE f.body_system='endocrine' AND f.chronicity='chronic';


Cross-Map Lookup

SELECT to_system, to_code, map_type, confidence
FROM code_mappings
WHERE from_code='E11.9' AND from_system='ICD10-CM';

9 Example Unified Response
{
  "query": "patient with long-standing high blood sugar",
  "matches": [
    {
      "code": "E11.9",
      "system": "ICD10-CM",
      "label": "Type 2 diabetes mellitus without complications",
      "similarity": 0.86,
      "facets": {
        "concept_type": "diagnosis",
        "body_system": "endocrine",
        "chronicity": "chronic",
        "risk_flag": true
      },
      "crossmaps": [
        {"to_system": "SNOMED", "to_code": "44054006", "map_type": "exact", "confidence": 0.95},
        {"to_system": "CPT", "to_code": "36416", "map_type": "billing", "confidence": 0.40}
      ]
    }
  ]
}
