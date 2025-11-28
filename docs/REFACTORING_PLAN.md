# Nuvii CDI Agent - Unified Platform Refactoring Plan

**Version:** 1.0
**Date:** 2025-11-27
**Author:** Nuvii Engineering
**Status:** Planning

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Goals & Objectives](#goals--objectives)
3. [Current State Analysis](#current-state-analysis)
4. [Target Architecture](#target-architecture)
5. [Phase 1: Project Structure Reorganization](#phase-1-project-structure-reorganization)
6. [Phase 2: Infrastructure Layer](#phase-2-infrastructure-layer)
7. [Phase 3: Domain Layer Implementation](#phase-3-domain-layer-implementation)
8. [Phase 4: Database Schema Extensions](#phase-4-database-schema-extensions)
9. [Phase 5: Adapters Layer - REST API](#phase-5-adapters-layer---rest-api)
10. [Phase 6: Adapters Layer - MCP Server](#phase-6-adapters-layer---mcp-server)
11. [Phase 7: Knowledge Base Migration](#phase-7-knowledge-base-migration)
12. [Phase 8: Frontend Updates](#phase-8-frontend-updates)
13. [Phase 9: Testing & Validation](#phase-9-testing--validation)
14. [Phase 10: Documentation & Deployment](#phase-10-documentation--deployment)
15. [Implementation Timeline](#implementation-timeline)
16. [Technical Decisions](#technical-decisions)
17. [Risk Assessment](#risk-assessment)

---

## Executive Summary

This document outlines the comprehensive refactoring plan to unify the Nuvii CDI Agent platform by:

1. **Integrating CDI Agent features** from the separate `../CDIAgent` project into this codebase
2. **Adding MCP Server capabilities** for Claude Desktop, VS Code, and LLM agent integration
3. **Restructuring the codebase** using clean architecture (Domain/Adapters/Infrastructure)
4. **Standardizing on PostgreSQL + pgvector** (removing ChromaDB dependency)
5. **Updating the frontend** to work with the new unified API

The refactoring will consolidate all clinical documentation integrity features into a single, maintainable platform that can be deployed via REST API, MCP server, or future integrations (Slack, Teams, FHIR).

---

## Goals & Objectives

### Primary Goals

| Goal | Description |
|------|-------------|
| **Unified Codebase** | Single repository for all CDI functionality |
| **Clean Architecture** | Domain-driven design with clear separation of concerns |
| **MCP Integration** | Enable LLM agents to use CDI tools via Model Context Protocol |
| **Scalable Infrastructure** | Support REST API, MCP, and future adapters |
| **No ChromaDB** | Standardize on PostgreSQL + pgvector for all vector operations |

### Non-Goals

- Backward compatibility with old API endpoints (frontend will be updated)
- Supporting multiple vector databases
- Mobile application support (future consideration)
- Real-time collaborative features (future consideration)

---

## Current State Analysis

### Nuvii CDI Agent (This Project)

| Component | Technology | Status |
|-----------|------------|--------|
| Backend Framework | FastAPI (Python 3.10+) | Production |
| Database | PostgreSQL 15 + pgvector | Production |
| Cache | Redis 7 | Production |
| Vector Search | pgvector (768-dim MedCPT) | Production |
| Full-text Search | PostgreSQL TSVECTOR + trigram | Production |
| Authentication | JWT + API Keys | Production |
| Billing | Stripe Integration | Production |
| LLM | Claude API (Anthropic) | Production |
| Frontend | Next.js 14 + TypeScript | Production |

**Current Features:**
- ICD-10 code search (semantic, hybrid, faceted)
- CPT/HCPCS procedure search
- Fee schedule pricing (CMS Medicare 2025)
- API key management
- Usage tracking & billing
- Developer dashboard

### CDI Agent Project (To Integrate)

| Component | Technology | Action |
|-----------|------------|--------|
| Backend Framework | FastAPI | Keep patterns |
| Vector Database | ChromaDB | **Remove - use PostgreSQL** |
| LLM | Mistral-7B (local) | **Replace with Claude API** |
| Embeddings | all-MiniLM-L6-v2 (384-dim) | **Replace with MedCPT (768-dim)** |
| Hybrid Search | BM25 + ChromaDB | **Replace with pgvector + TSVECTOR** |

**Features to Port:**
- CDI query generation
- Documentation gap detection
- Investigation recommendations
- Revenue optimization (E/M coding, DRG)
- HEDIS quality measures (19 measures)
- Clinical entity extraction

---

## Target Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ADAPTERS LAYER                                  │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│     REST API        │     MCP Server      │     Future: Slack/Teams/FHIR    │
│   (FastAPI)         │   (JSON-RPC/STDIO)  │                                 │
│                     │                     │                                 │
│  /api/v1/cdi/*      │  analyze_note       │                                 │
│  /api/v1/codes/*    │  generate_query     │                                 │
│  /api/v1/fees/*     │  search_codes       │                                 │
│  /api/v1/revenue/*  │  calculate_fees     │                                 │
│  /api/v1/quality/*  │  optimize_revenue   │                                 │
└─────────┬───────────┴──────────┬──────────┴─────────────────────────────────┘
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOMAIN LAYER                                    │
│                     (Pure Business Logic - No I/O)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Coding     │  │Documentation │  │    Query     │  │   Revenue    │    │
│  │   Helper     │  │    Gaps      │  │  Generation  │  │ Optimization │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Semantic   │  │    HEDIS     │  │    Entity    │  │     Fee      │    │
│  │   Search     │  │  Evaluation  │  │  Extraction  │  │   Schedule   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                         Common Module                             │      │
│  │         (Scoring, Heuristics, Validation, Utilities)             │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INFRASTRUCTURE LAYER                               │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│     Database        │        LLM          │         Config & Logging        │
│                     │                     │                                 │
│  PostgreSQL 15      │  Claude API         │  AWS Parameter Store            │
│  + pgvector         │  (primary)          │  Environment Variables          │
│  + TSVECTOR         │                     │  Structured Logging             │
│  Redis (cache)      │  OpenAI (fallback)  │                                 │
│                     │  Local (optional)   │                                 │
└─────────────────────┴─────────────────────┴─────────────────────────────────┘
```

### Directory Structure (Target)

```
nuvii-cdi-agent/
│
├── backend/
│   │
│   ├── domain/                           # Core Business Logic
│   │   ├── __init__.py
│   │   │
│   │   ├── coding_helper/                # ICD-10/CPT code assistance
│   │   │   ├── __init__.py
│   │   │   ├── code_suggester.py         # Suggest codes from text
│   │   │   ├── code_validator.py         # Validate code accuracy
│   │   │   ├── code_comparison.py        # Compare/relate codes
│   │   │   └── diagnosis_completeness.py # Check diagnosis completeness
│   │   │
│   │   ├── documentation_gaps/           # Clinical documentation gaps
│   │   │   ├── __init__.py
│   │   │   ├── gap_detector.py           # Main gap detection
│   │   │   ├── specificity_analyzer.py   # Missing specificity
│   │   │   ├── acuity_analyzer.py        # Missing acuity indicators
│   │   │   ├── comorbidity_checker.py    # Missing co-morbidities
│   │   │   └── medical_necessity.py      # Medical necessity gaps
│   │   │
│   │   ├── query_generation/             # CDI query generation
│   │   │   ├── __init__.py
│   │   │   ├── query_generator.py        # Generate physician queries
│   │   │   ├── prompt_templates.py       # CDI prompt templates
│   │   │   ├── query_validator.py        # Validate query quality
│   │   │   └── query_styles.py           # Open-ended, yes/no, etc.
│   │   │
│   │   ├── revenue_optimization/         # Revenue & coding optimization
│   │   │   ├── __init__.py
│   │   │   ├── revenue_analyzer.py       # Revenue gap analysis
│   │   │   ├── em_coding.py              # E/M code recommendations
│   │   │   ├── hcc_evaluator.py          # HCC risk scoring (V24, V28)
│   │   │   ├── drg_optimizer.py          # DRG upgrade suggestions
│   │   │   └── test_gap_analyzer.py      # Missing tests analysis
│   │   │
│   │   ├── hedis_evaluation/             # HEDIS quality measures
│   │   │   ├── __init__.py
│   │   │   ├── hedis_evaluator.py        # Main HEDIS evaluator
│   │   │   ├── measure_definitions.py    # 19 measure configurations
│   │   │   ├── exclusion_criteria.py     # Exclusion logic
│   │   │   └── value_based_eval.py       # Value-based evaluation
│   │   │
│   │   ├── entity_extraction/            # Clinical entity extraction
│   │   │   ├── __init__.py
│   │   │   ├── clinical_extractor.py     # Diagnoses, symptoms, meds
│   │   │   ├── vital_extractor.py        # Vital signs extraction
│   │   │   ├── lab_extractor.py          # Lab values extraction
│   │   │   ├── procedure_extractor.py    # Procedures mentioned
│   │   │   └── screening_extractor.py    # Screenings documented
│   │   │
│   │   ├── semantic_search/              # Vector & text search
│   │   │   ├── __init__.py
│   │   │   ├── icd10_search.py           # ICD-10 search logic
│   │   │   ├── procedure_search.py       # CPT/HCPCS search logic
│   │   │   ├── guideline_search.py       # CDI guidelines search
│   │   │   ├── hybrid_retriever.py       # Combined vector + text
│   │   │   └── reranker.py               # Result re-ranking
│   │   │
│   │   ├── fee_schedule/                 # Fee schedule & pricing
│   │   │   ├── __init__.py
│   │   │   ├── price_calculator.py       # Calculate reimbursement
│   │   │   ├── locality_mapper.py        # ZIP to locality mapping
│   │   │   ├── rvu_calculator.py         # RVU calculations
│   │   │   ├── contract_analyzer.py      # Contract pricing analysis
│   │   │   └── fee_comparator.py         # Compare fee schedules
│   │   │
│   │   └── common/                       # Shared utilities
│   │       ├── __init__.py
│   │       ├── scoring.py                # Confidence scoring
│   │       ├── validation.py             # Input validation
│   │       ├── heuristics.py             # Clinical heuristics
│   │       └── text_utils.py             # Text processing utilities
│   │
│   ├── adapters/                         # Interface Adapters
│   │   │
│   │   ├── api/                          # REST API (FastAPI)
│   │   │   ├── __init__.py
│   │   │   ├── main.py                   # FastAPI app initialization
│   │   │   │
│   │   │   ├── routes/                   # API endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py               # Authentication endpoints
│   │   │   │   ├── api_keys.py           # API key management
│   │   │   │   ├── codes.py              # ICD-10/CPT search endpoints
│   │   │   │   ├── cdi.py                # CDI analysis endpoints
│   │   │   │   ├── revenue.py            # Revenue optimization endpoints
│   │   │   │   ├── quality.py            # HEDIS/quality endpoints
│   │   │   │   ├── fees.py               # Fee schedule endpoints
│   │   │   │   ├── billing.py            # Stripe billing endpoints
│   │   │   │   ├── usage.py              # Usage tracking endpoints
│   │   │   │   └── admin.py              # Admin endpoints
│   │   │   │
│   │   │   ├── middleware/               # API middleware
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py               # JWT authentication
│   │   │   │   ├── api_key.py            # API key verification
│   │   │   │   └── rate_limit.py         # Rate limiting
│   │   │   │
│   │   │   ├── schemas/                  # Pydantic schemas
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py               # Auth request/response
│   │   │   │   ├── codes.py              # Code search schemas
│   │   │   │   ├── cdi.py                # CDI analysis schemas
│   │   │   │   ├── revenue.py            # Revenue schemas
│   │   │   │   ├── quality.py            # Quality measure schemas
│   │   │   │   ├── fees.py               # Fee schedule schemas
│   │   │   │   └── common.py             # Shared schemas
│   │   │   │
│   │   │   └── dependencies.py           # FastAPI dependencies
│   │   │
│   │   ├── mcp/                          # MCP Server
│   │   │   ├── __init__.py
│   │   │   ├── server.py                 # MCP server initialization
│   │   │   │
│   │   │   ├── tools/                    # MCP tool implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analyze_note.py       # Clinical note analysis
│   │   │   │   ├── generate_query.py     # CDI query generation
│   │   │   │   ├── search_icd10.py       # ICD-10 semantic search
│   │   │   │   ├── search_cpt.py         # CPT/HCPCS search
│   │   │   │   ├── calculate_fees.py     # Fee schedule pricing
│   │   │   │   ├── optimize_revenue.py   # Revenue optimization
│   │   │   │   ├── evaluate_hedis.py     # HEDIS evaluation
│   │   │   │   └── extract_entities.py   # Entity extraction
│   │   │   │
│   │   │   └── schemas/                  # MCP tool schemas
│   │   │       ├── __init__.py
│   │   │       └── tool_definitions.py   # JSON Schema definitions
│   │   │
│   │   └── cli/                          # CLI tool (optional)
│   │       ├── __init__.py
│   │       └── cli.py                    # Command-line interface
│   │
│   ├── infrastructure/                   # External Dependencies
│   │   │
│   │   ├── db/                           # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── postgres.py               # PostgreSQL connection
│   │   │   ├── redis.py                  # Redis connection
│   │   │   │
│   │   │   ├── models/                   # SQLAlchemy models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py               # User model
│   │   │   │   ├── api_key.py            # API key model
│   │   │   │   ├── plan.py               # Subscription plan model
│   │   │   │   ├── subscription.py       # Stripe subscription model
│   │   │   │   ├── usage_log.py          # Usage logging model
│   │   │   │   ├── icd10_code.py         # ICD-10 codes
│   │   │   │   ├── procedure_code.py     # CPT/HCPCS codes
│   │   │   │   ├── fee_schedule.py       # Fee schedule models
│   │   │   │   ├── cdi_guideline.py      # CDI guidelines (NEW)
│   │   │   │   ├── investigation.py      # Investigation protocols (NEW)
│   │   │   │   ├── em_code.py            # E/M codes (NEW)
│   │   │   │   ├── cdi_query_history.py  # CDI query history (NEW)
│   │   │   │   └── hedis_evaluation.py   # HEDIS results (NEW)
│   │   │   │
│   │   │   ├── repositories/             # Data access layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── icd10_repository.py
│   │   │   │   ├── procedure_repository.py
│   │   │   │   ├── guideline_repository.py
│   │   │   │   ├── fee_schedule_repository.py
│   │   │   │   └── user_repository.py
│   │   │   │
│   │   │   └── migrations/               # Alembic migrations
│   │   │       ├── env.py
│   │   │       ├── script.py.mako
│   │   │       └── versions/
│   │   │
│   │   ├── llm/                          # LLM integrations
│   │   │   ├── __init__.py
│   │   │   ├── base_engine.py            # Abstract LLM interface
│   │   │   ├── anthropic_engine.py       # Claude API (primary)
│   │   │   ├── openai_engine.py          # OpenAI GPT (fallback)
│   │   │   ├── embedding_engine.py       # MedCPT embeddings
│   │   │   └── local_engine.py           # Local models (optional)
│   │   │
│   │   ├── config/                       # Configuration
│   │   │   ├── __init__.py
│   │   │   ├── settings.py               # App settings
│   │   │   └── parameter_store.py        # AWS Parameter Store
│   │   │
│   │   └── logging/                      # Logging
│   │       ├── __init__.py
│   │       └── logger.py                 # Structured logging
│   │
│   ├── scripts/                          # Utility scripts
│   │   ├── load_icd10_data.py
│   │   ├── load_procedure_data.py
│   │   ├── load_fee_schedule_data.py
│   │   ├── load_cdi_guidelines.py        # NEW
│   │   ├── load_investigation_protocols.py # NEW
│   │   ├── load_em_codes.py              # NEW
│   │   ├── generate_embeddings.py
│   │   └── migrate_cdi_agent_data.py     # NEW
│   │
│   ├── tests/                            # Test suite
│   │   ├── domain/
│   │   ├── adapters/
│   │   ├── infrastructure/
│   │   └── integration/
│   │
│   ├── data/                             # Data files
│   │   ├── icd10/
│   │   ├── procedures/
│   │   ├── fee_schedules/
│   │   ├── cdi_guidelines/               # NEW
│   │   ├── investigations/               # NEW
│   │   └── em_codes/                     # NEW
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── alembic.ini
│
├── frontend/                             # Next.js Frontend
│   ├── app/
│   ├── lib/
│   ├── components/
│   └── ...
│
├── docs/                                 # Documentation
│   ├── requirements/
│   ├── api/
│   ├── architecture.md
│   └── REFACTORING_PLAN.md              # This document
│
├── infrastructure/                       # IaC (Terraform)
│
├── CLAUDE.md
├── README.md
└── Refactor.md
```

---

## Phase 1: Project Structure Reorganization

### Objective
Create the new directory structure and move existing files without breaking anything.

### Tasks

#### 1.1 Create New Directory Structure

```bash
# Create domain layer directories
mkdir -p backend/domain/{coding_helper,documentation_gaps,query_generation}
mkdir -p backend/domain/{revenue_optimization,hedis_evaluation,entity_extraction}
mkdir -p backend/domain/{semantic_search,fee_schedule,common}

# Create adapters layer directories
mkdir -p backend/adapters/api/{routes,middleware,schemas}
mkdir -p backend/adapters/mcp/{tools,schemas}
mkdir -p backend/adapters/cli

# Create infrastructure layer directories
mkdir -p backend/infrastructure/db/{models,repositories,migrations}
mkdir -p backend/infrastructure/{llm,config,logging}

# Create data directories for CDI
mkdir -p backend/data/{cdi_guidelines,investigations,em_codes}
```

#### 1.2 Move Existing Files

| Source | Destination |
|--------|-------------|
| `app/main.py` | `adapters/api/main.py` |
| `app/api/v1/*.py` | `adapters/api/routes/*.py` |
| `app/middleware/*.py` | `adapters/api/middleware/*.py` |
| `app/schemas/*.py` | `adapters/api/schemas/*.py` |
| `app/models/*.py` | `infrastructure/db/models/*.py` |
| `app/services/icd10_search_service.py` | `domain/semantic_search/icd10_search.py` |
| `app/services/procedure_search_service.py` | `domain/semantic_search/procedure_search.py` |
| `app/services/fee_schedule_service.py` | `domain/fee_schedule/price_calculator.py` |
| `app/services/embedding_service.py` | `infrastructure/llm/embedding_engine.py` |
| `app/database.py` | `infrastructure/db/postgres.py` |
| `app/config.py` | `infrastructure/config/settings.py` |
| `app/parameter_store.py` | `infrastructure/config/parameter_store.py` |
| `alembic/` | `infrastructure/db/migrations/` |

#### 1.3 Update Import Paths

- Update all Python imports to reflect new structure
- Update `alembic.ini` to point to new migrations location
- Update `Dockerfile` and `docker-compose.yml` paths

#### 1.4 Create `__init__.py` Files

Create proper `__init__.py` files for all new packages with appropriate exports.

### Deliverables
- [ ] New directory structure created
- [ ] All existing files moved to new locations
- [ ] Import paths updated
- [ ] Application starts and existing tests pass

---

## Phase 2: Infrastructure Layer

### Objective
Establish the infrastructure layer with database, LLM, and configuration abstractions.

### Tasks

#### 2.1 Database Layer (`infrastructure/db/`)

**postgres.py** - Database connection management
```python
# Core database setup
- AsyncSession factory
- Connection pooling
- Health check methods
```

**redis.py** - Cache connection management
```python
# Redis connection
- Connection pool
- Cache utilities
```

**repositories/** - Data access patterns
```python
# Repository pattern for each domain
- ICD10Repository
- ProcedureRepository
- GuidelineRepository
- FeeScheduleRepository
- UserRepository
```

#### 2.2 LLM Layer (`infrastructure/llm/`)

**base_engine.py** - Abstract LLM interface
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class LLMEngine(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    async def generate_with_context(
        self,
        query: str,
        context_documents: List[str],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text with RAG context."""
        pass

    @abstractmethod
    async def extract_structured(
        self,
        text: str,
        schema: dict
    ) -> dict:
        """Extract structured data from text."""
        pass
```

**anthropic_engine.py** - Claude API implementation (primary)
```python
# Primary LLM engine
- Claude 3.5 Sonnet integration
- Streaming support
- Token counting
- Error handling with retries
```

**openai_engine.py** - OpenAI implementation (fallback)
```python
# Fallback LLM engine
- GPT-4 integration
- Compatible interface
```

**embedding_engine.py** - Embedding generation
```python
# MedCPT embedding model
- Batch embedding generation
- Caching for repeated texts
- 768-dimensional vectors
```

#### 2.3 Configuration Layer (`infrastructure/config/`)

**settings.py** - Application configuration
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "Nuvii CDI Agent"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str
    redis_url: str

    # Authentication
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # LLM
    anthropic_api_key: str
    claude_model: str = "claude-3-5-sonnet-20241022"
    openai_api_key: Optional[str] = None

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 10000

    # Code Versions
    default_icd10_version_year: int = 2026
    default_procedure_version_year: int = 2025
    default_fee_schedule_year: int = 2025

    class Config:
        env_file = ".env"
```

### Deliverables
- [ ] Database connection abstraction complete
- [ ] Repository pattern implemented
- [ ] LLM engine interface and implementations
- [ ] Configuration management with Pydantic
- [ ] All existing functionality works with new infrastructure

---

## Phase 3: Domain Layer Implementation

### Objective
Implement all domain modules with pure business logic.

### Tasks

#### 3.1 Semantic Search (`domain/semantic_search/`)

**icd10_search.py**
```python
class ICD10SearchService:
    async def search_by_code(code: str) -> List[ICD10Code]
    async def search_by_text(query: str, limit: int = 10) -> List[ICD10Code]
    async def search_semantic(query: str, limit: int = 10) -> List[ICD10Code]
    async def search_hybrid(query: str, semantic_weight: float = 0.7) -> List[ICD10Code]
    async def search_faceted(filters: dict, query: Optional[str]) -> List[ICD10Code]
```

**procedure_search.py**
```python
class ProcedureSearchService:
    async def search_by_code(code: str) -> List[ProcedureCode]
    async def search_by_text(query: str) -> List[ProcedureCode]
    async def search_semantic(query: str) -> List[ProcedureCode]
    async def search_hybrid(query: str) -> List[ProcedureCode]
```

**guideline_search.py** (NEW)
```python
class GuidelineSearchService:
    async def search_guidelines(query: str, specialty: Optional[str]) -> List[Guideline]
    async def get_by_condition(condition: str) -> List[Guideline]
```

**hybrid_retriever.py**
```python
class HybridRetriever:
    async def retrieve(
        query: str,
        collections: List[str],
        vector_weight: float = 0.6,
        top_k: int = 10
    ) -> List[Document]
```

#### 3.2 Coding Helper (`domain/coding_helper/`)

**code_suggester.py**
```python
class CodeSuggester:
    async def suggest_from_text(
        clinical_text: str,
        code_types: List[str] = ["icd10", "cpt"]
    ) -> CodeSuggestionResult:
        """
        Analyze clinical text and suggest appropriate codes.
        Uses LLM + semantic search for accurate suggestions.
        """

    async def suggest_icd10(text: str) -> List[ICD10Suggestion]
    async def suggest_cpt(text: str) -> List[CPTSuggestion]
```

**diagnosis_completeness.py**
```python
class DiagnosisCompletenessChecker:
    async def check_completeness(
        diagnoses: List[str],
        clinical_note: str
    ) -> CompletenessResult:
        """Check if all conditions in note are properly coded."""
```

#### 3.3 Documentation Gaps (`domain/documentation_gaps/`)

**gap_detector.py**
```python
class DocumentationGapDetector:
    async def detect_gaps(
        clinical_note: str,
        existing_codes: Optional[List[str]] = None
    ) -> GapDetectionResult:
        """
        Analyze clinical note for documentation gaps.

        Returns:
            - missing_specificity: List of conditions needing more detail
            - missing_acuity: List of conditions needing acuity
            - missing_comorbidities: Potentially missing related conditions
            - documentation_risks: Compliance/coding risks
        """
```

**specificity_analyzer.py**
```python
class SpecificityAnalyzer:
    async def analyze(note: str) -> List[SpecificityGap]:
        """
        Find conditions documented without required specificity.
        Example: "diabetes" without type specification
        """
```

**acuity_analyzer.py**
```python
class AcuityAnalyzer:
    async def analyze(note: str) -> List[AcuityGap]:
        """
        Find conditions missing severity/acuity indicators.
        Example: "malnutrition" without severity level
        """
```

#### 3.4 Query Generation (`domain/query_generation/`)

**query_generator.py**
```python
class CDIQueryGenerator:
    async def generate_query(
        clinical_note: str,
        gap_type: Optional[str] = None,
        style: QueryStyle = QueryStyle.OPEN_ENDED
    ) -> CDIQueryResult:
        """
        Generate physician-facing CDI query.

        Args:
            clinical_note: The clinical documentation
            gap_type: Specific gap to address (or None for auto-detect)
            style: Query style (open_ended, yes_no, documentation_based)

        Returns:
            - query: The generated query text
            - source_documents: Supporting guidelines
            - validation: Quality validation result
            - confidence: Confidence score
        """
```

**query_validator.py**
```python
class QueryValidator:
    def validate(query: str) -> ValidationResult:
        """
        Validate CDI query quality.

        Checks:
            - Non-leading (doesn't suggest diagnosis)
            - Clinical context present
            - Professional tone
            - Actionable
        """
```

#### 3.5 Revenue Optimization (`domain/revenue_optimization/`)

**revenue_analyzer.py**
```python
class RevenueAnalyzer:
    async def analyze(
        clinical_note: str,
        documented_codes: Optional[List[str]] = None
    ) -> RevenueAnalysisResult:
        """
        Comprehensive revenue analysis.

        Returns:
            - documented_revenue: Revenue from documented codes
            - missing_revenue: Potential revenue from gaps
            - optimization_opportunities: Prioritized list
            - capture_rate: Current capture percentage
        """
```

**em_coding.py**
```python
class EMCodingAnalyzer:
    async def analyze(
        clinical_note: str,
        setting: str = "outpatient",
        patient_type: str = "established"
    ) -> EMCodingResult:
        """
        E/M code analysis based on 2021 guidelines.

        Returns:
            - recommended_code: Best E/M code
            - current_level: Documented level
            - potential_upgrade: Possible upgrade
            - documentation_gaps: What's needed for upgrade
            - mdm_analysis: Medical Decision Making breakdown
        """
```

**hcc_evaluator.py**
```python
class HCCEvaluator:
    async def evaluate(
        diagnoses: List[str],
        model_version: str = "V28"
    ) -> HCCResult:
        """
        HCC risk adjustment analysis.

        Returns:
            - hcc_codes: Mapped HCC codes
            - risk_score: Calculated RAF score
            - opportunities: Under-coded conditions
            - documentation_needed: For accurate capture
        """
```

**drg_optimizer.py**
```python
class DRGOptimizer:
    async def analyze(
        principal_diagnosis: str,
        secondary_diagnoses: List[str],
        procedures: List[str]
    ) -> DRGResult:
        """
        DRG optimization analysis.

        Returns:
            - current_drg: Estimated current DRG
            - potential_drg: Possible upgrade
            - revenue_impact: Dollar difference
            - documentation_improvements: What to add
        """
```

#### 3.6 HEDIS Evaluation (`domain/hedis_evaluation/`)

**hedis_evaluator.py**
```python
class HEDISEvaluator:
    async def evaluate(
        clinical_note: str,
        patient_age: int,
        patient_gender: str,
        icd10_codes: Optional[List[str]] = None
    ) -> HEDISResult:
        """
        Evaluate against 19 HEDIS measures.

        Measures:
            - CBP: Controlling Blood Pressure
            - CDC: Comprehensive Diabetes Care
            - BCS: Breast Cancer Screening
            - COL: Colorectal Cancer Screening
            - BMI: Body Mass Index
            - DEP: Depression Screening
            - CHL: Chlamydia Screening
            - WCC: Well-Child Visits
            - CIS: Childhood Immunization
            - IMA: Immunizations for Adolescents
            - AAP: Adults Access to Preventive
            - AWC: Adolescent Well-Care
            - AMM: Antidepressant Medication Management
            - ADD: ADHD Medication Follow-up
            - FUH: Follow-up After Hospitalization
            - FUM: Follow-up After ED Mental Health
            - FUA: Follow-up After ED Alcohol
            - PPC: Prenatal/Postpartum Care
            - PCE: Pharmacotherapy for COPD
        """
```

**measure_definitions.py**
```python
# Configuration for all 19 HEDIS measures
HEDIS_MEASURES = {
    "CBP": {
        "name": "Controlling Blood Pressure",
        "age_range": (18, 85),
        "targets": {"systolic": 140, "diastolic": 90},
        "exclusions": ["pregnancy", "esrd", "hospice"]
    },
    # ... 18 more measures
}
```

#### 3.7 Entity Extraction (`domain/entity_extraction/`)

**clinical_extractor.py**
```python
class ClinicalEntityExtractor:
    async def extract(clinical_note: str) -> ExtractionResult:
        """
        Extract clinical entities from note.

        Returns:
            - diagnoses: List[Diagnosis]
            - symptoms: List[Symptom]
            - medications: List[Medication]
            - labs: List[LabResult]
            - vitals: List[VitalSign]
            - procedures: List[Procedure]
            - screenings: List[Screening]
        """
```

#### 3.8 Fee Schedule (`domain/fee_schedule/`)

**price_calculator.py**
```python
class FeeSchedulePriceCalculator:
    async def calculate_price(
        code: str,
        zip_code: str,
        year: int = 2025,
        facility: bool = False
    ) -> PriceResult:
        """
        Calculate Medicare reimbursement for a code.

        Returns:
            - code: The procedure code
            - price: Calculated reimbursement
            - locality: CMS locality info
            - rvu_breakdown: Work, PE, MP RVUs
            - conversion_factor: Applied CF
        """
```

**locality_mapper.py**
```python
class LocalityMapper:
    async def get_locality(zip_code: str) -> LocalityInfo:
        """Map ZIP code to CMS locality with GPCI values."""
```

**contract_analyzer.py**
```python
class ContractAnalyzer:
    async def analyze_contract(
        codes: List[str],
        contract_rates: dict,
        medicare_rates: dict
    ) -> ContractAnalysisResult:
        """Compare contract rates to Medicare baseline."""
```

**fee_comparator.py**
```python
class FeeComparator:
    async def compare_schedules(
        codes: List[str],
        schedule_a: str,
        schedule_b: str
    ) -> ComparisonResult:
        """Compare two fee schedules for given codes."""
```

### Deliverables
- [ ] All domain modules implemented
- [ ] Unit tests for each module
- [ ] No external I/O in domain layer (uses repositories)
- [ ] Documentation for each service

---

## Phase 4: Database Schema Extensions

### Objective
Add new database tables for CDI functionality.

### Tasks

#### 4.1 New Tables

**CDI Guidelines Table**
```sql
CREATE TABLE cdi_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    title VARCHAR(500),
    category VARCHAR(100),
    specialty VARCHAR(100),
    condition VARCHAR(200),
    source VARCHAR(200),
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cdi_guidelines_embedding ON cdi_guidelines
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_cdi_guidelines_category ON cdi_guidelines(category);
CREATE INDEX idx_cdi_guidelines_condition ON cdi_guidelines(condition);
```

**Investigation Protocols Table**
```sql
CREATE TABLE investigation_protocols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    condition VARCHAR(200) NOT NULL,
    icd10_codes TEXT[],
    severity_level VARCHAR(50),
    test_name VARCHAR(300) NOT NULL,
    cpt_code VARCHAR(20),
    estimated_cost DECIMAL(10,2),
    evidence_grade VARCHAR(10),
    timing VARCHAR(200),
    rationale TEXT,
    required BOOLEAN DEFAULT FALSE,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_investigation_condition ON investigation_protocols(condition);
CREATE INDEX idx_investigation_severity ON investigation_protocols(severity_level);
CREATE INDEX idx_investigation_embedding ON investigation_protocols
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

**E/M Codes Table**
```sql
CREATE TABLE em_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    setting VARCHAR(50) NOT NULL,  -- inpatient, outpatient, ed, etc.
    patient_type VARCHAR(50),      -- new, established, initial, subsequent
    level INTEGER,
    mdm_level VARCHAR(20),
    time_range_min INTEGER,
    time_range_max INTEGER,
    reimbursement DECIMAL(10,2),
    requirements JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(code, setting, patient_type)
);
```

**CDI Query History Table**
```sql
CREATE TABLE cdi_query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    clinical_note TEXT NOT NULL,
    clinical_note_hash VARCHAR(64),  -- For deduplication
    generated_query TEXT,
    gap_type VARCHAR(100),
    validation_score DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    source_documents JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cdi_history_user ON cdi_query_history(user_id);
CREATE INDEX idx_cdi_history_created ON cdi_query_history(created_at);
```

**HEDIS Evaluation Results Table**
```sql
CREATE TABLE hedis_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    patient_age INTEGER,
    patient_gender VARCHAR(20),
    icd10_codes TEXT[],
    note_hash VARCHAR(64),

    -- Extracted entities
    diagnoses JSONB,
    vitals JSONB,
    labs JSONB,
    screenings JSONB,

    -- Results
    measure_results JSONB,
    generated_queries JSONB,
    completeness_score DECIMAL(3,2),

    -- Confidence
    extraction_confidence DECIMAL(3,2),
    measure_confidence DECIMAL(3,2),

    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hedis_user ON hedis_evaluations(user_id);
CREATE INDEX idx_hedis_created ON hedis_evaluations(created_at);
```

**Revenue Analysis History Table**
```sql
CREATE TABLE revenue_analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,

    clinical_note_hash VARCHAR(64),
    condition VARCHAR(200),
    severity VARCHAR(50),

    -- Test Analysis
    documented_tests JSONB,
    recommended_tests JSONB,
    missing_tests JSONB,

    -- Revenue Analysis
    documented_revenue DECIMAL(12,2),
    missing_revenue DECIMAL(12,2),
    total_opportunity DECIMAL(12,2),
    capture_rate DECIMAL(5,2),

    -- E/M Coding
    em_coding_result JSONB,

    -- DRG
    drg_analysis JSONB,

    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4.2 Alembic Migrations

Create migration files for all new tables:
- `xxx_add_cdi_guidelines_table.py`
- `xxx_add_investigation_protocols_table.py`
- `xxx_add_em_codes_table.py`
- `xxx_add_cdi_query_history_table.py`
- `xxx_add_hedis_evaluations_table.py`
- `xxx_add_revenue_analysis_history_table.py`

#### 4.3 SQLAlchemy Models

Create models in `infrastructure/db/models/`:
- `cdi_guideline.py`
- `investigation.py`
- `em_code.py`
- `cdi_query_history.py`
- `hedis_evaluation.py`
- `revenue_analysis.py`

### Deliverables
- [ ] All migration files created
- [ ] SQLAlchemy models created
- [ ] Migrations run successfully
- [ ] Indexes verified for performance

---

## Phase 5: Adapters Layer - REST API

### Objective
Create new API endpoints exposing all domain functionality.

### Tasks

#### 5.1 New Route Files

**routes/codes.py** - Code Search Endpoints
```python
# ICD-10 Endpoints
GET  /api/v1/codes/icd10/search          # Text search
GET  /api/v1/codes/icd10/semantic        # Semantic search
GET  /api/v1/codes/icd10/hybrid          # Hybrid search
GET  /api/v1/codes/icd10/{code}          # Get by code
GET  /api/v1/codes/icd10/faceted         # Faceted search

# CPT/HCPCS Endpoints
GET  /api/v1/codes/procedure/search      # Text search
GET  /api/v1/codes/procedure/semantic    # Semantic search
GET  /api/v1/codes/procedure/hybrid      # Hybrid search
GET  /api/v1/codes/procedure/{code}      # Get by code

# Suggestions
POST /api/v1/codes/suggest               # Suggest codes from text
```

**routes/cdi.py** - CDI Analysis Endpoints
```python
# Note Analysis
POST /api/v1/cdi/analyze                 # Full note analysis
POST /api/v1/cdi/gaps                    # Documentation gap detection
POST /api/v1/cdi/entities                # Entity extraction only

# Query Generation
POST /api/v1/cdi/generate-query          # Generate CDI query
GET  /api/v1/cdi/query-history           # User's query history

# Guidelines
GET  /api/v1/cdi/guidelines              # Search guidelines
GET  /api/v1/cdi/guidelines/{condition}  # Get by condition
```

**routes/revenue.py** - Revenue Optimization Endpoints
```python
# Revenue Analysis
POST /api/v1/revenue/analyze             # Full revenue analysis
POST /api/v1/revenue/em-coding           # E/M coding only
POST /api/v1/revenue/hcc                 # HCC evaluation
POST /api/v1/revenue/drg                 # DRG optimization

# Investigations
POST /api/v1/revenue/investigations      # Recommend investigations
GET  /api/v1/revenue/investigation-protocols/{condition}  # Get protocols
```

**routes/quality.py** - Quality Measure Endpoints
```python
# HEDIS Evaluation
POST /api/v1/quality/hedis               # Full HEDIS evaluation
GET  /api/v1/quality/hedis/measures      # List available measures
GET  /api/v1/quality/hedis/history       # User's evaluation history

# Comprehensive
POST /api/v1/quality/comprehensive       # All quality analysis
```

**routes/fees.py** - Fee Schedule Endpoints
```python
# Price Lookup
GET  /api/v1/fees/price                  # Get price for code + ZIP
GET  /api/v1/fees/prices/bulk            # Bulk price lookup
GET  /api/v1/fees/locality/{zip_code}    # Get locality info

# Analysis
POST /api/v1/fees/contract-analysis      # Analyze contract vs Medicare
POST /api/v1/fees/compare                # Compare fee schedules

# RVU
GET  /api/v1/fees/rvu/{code}             # Get RVU breakdown
```

#### 5.2 Pydantic Schemas

**schemas/cdi.py**
```python
class NoteAnalysisRequest(BaseModel):
    clinical_note: str = Field(..., min_length=10, max_length=50000)
    include_suggestions: bool = True
    include_gaps: bool = True
    include_entities: bool = True

class NoteAnalysisResponse(BaseModel):
    findings: List[str]
    documentation_gaps: List[DocumentationGap]
    recommended_codes: List[CodeSuggestion]
    entities: ExtractedEntities
    confidence_score: float

class CDIQueryRequest(BaseModel):
    clinical_note: str
    gap_type: Optional[str] = None
    query_style: QueryStyle = QueryStyle.OPEN_ENDED

class CDIQueryResponse(BaseModel):
    query: str
    source_documents: List[str]
    validation: ValidationResult
    confidence: float
    retrieval_confidence: float
```

**schemas/revenue.py**
```python
class RevenueAnalysisRequest(BaseModel):
    clinical_note: str
    setting: str = "outpatient"
    patient_type: str = "established"
    include_em_coding: bool = True
    include_drg: bool = False

class RevenueAnalysisResponse(BaseModel):
    condition: str
    severity: str
    test_analysis: TestAnalysis
    revenue_analysis: RevenueBreakdown
    em_coding: Optional[EMCodingResult]
    drg_optimization: Optional[DRGResult]
    total_opportunity: Decimal
```

**schemas/quality.py**
```python
class HEDISRequest(BaseModel):
    clinical_note: str
    patient_age: int = Field(..., ge=0, le=120)
    patient_gender: str
    icd10_codes: Optional[List[str]] = None
    generate_queries: bool = True

class HEDISResponse(BaseModel):
    diagnoses: List[str]
    vitals: Dict[str, str]
    labs: Dict[str, str]
    screenings: Dict[str, bool]
    measure_results: Dict[str, bool]
    generated_queries: Optional[Dict[str, str]]
    completeness_score: float
    missing_elements: List[str]
```

**schemas/fees.py**
```python
class PriceRequest(BaseModel):
    code: str
    zip_code: str
    year: int = 2025
    facility: bool = False

class PriceResponse(BaseModel):
    code: str
    description: str
    price: Decimal
    locality: LocalityInfo
    rvu_breakdown: RVUBreakdown
    conversion_factor: Decimal

class ContractAnalysisRequest(BaseModel):
    codes: List[str]
    contract_rates: Dict[str, Decimal]
    zip_code: str

class ContractAnalysisResponse(BaseModel):
    comparisons: List[CodeComparison]
    total_medicare: Decimal
    total_contract: Decimal
    variance_percentage: float
```

#### 5.3 Update API Main

**adapters/api/main.py**
```python
from fastapi import FastAPI
from adapters.api.routes import (
    auth, api_keys, codes, cdi, revenue, quality, fees, billing, usage, admin
)

app = FastAPI(
    title="Nuvii CDI Agent API",
    description="Clinical Documentation Integrity & Medical Coding API",
    version="2.0.0"
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])
app.include_router(codes.router, prefix="/api/v1/codes", tags=["Code Search"])
app.include_router(cdi.router, prefix="/api/v1/cdi", tags=["CDI Analysis"])
app.include_router(revenue.router, prefix="/api/v1/revenue", tags=["Revenue Optimization"])
app.include_router(quality.router, prefix="/api/v1/quality", tags=["Quality Measures"])
app.include_router(fees.router, prefix="/api/v1/fees", tags=["Fee Schedule"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(usage.router, prefix="/api/v1/usage", tags=["Usage"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
```

### Deliverables
- [ ] All route files created
- [ ] Pydantic schemas defined
- [ ] OpenAPI documentation generates correctly
- [ ] All endpoints tested via Swagger UI

---

## Phase 6: Adapters Layer - MCP Server

### Objective
Implement MCP server with tools for LLM agent integration.

### Tasks

#### 6.1 MCP Server Setup

**adapters/mcp/server.py**
```python
from mcp import Server, Tool
from mcp.types import TextContent
import asyncio
import json

from adapters.mcp.tools import (
    analyze_note,
    generate_query,
    search_icd10,
    search_cpt,
    calculate_fees,
    optimize_revenue,
    evaluate_hedis,
    extract_entities
)

server = Server("nuvii-cdi-agent")

# Register all tools
server.add_tool(analyze_note.tool)
server.add_tool(generate_query.tool)
server.add_tool(search_icd10.tool)
server.add_tool(search_cpt.tool)
server.add_tool(calculate_fees.tool)
server.add_tool(optimize_revenue.tool)
server.add_tool(evaluate_hedis.tool)
server.add_tool(extract_entities.tool)

async def main():
    async with server.run_stdio():
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 6.2 MCP Tools

**tools/analyze_note.py**
```python
from mcp import Tool
from domain.documentation_gaps import DocumentationGapDetector
from domain.entity_extraction import ClinicalEntityExtractor
from domain.coding_helper import CodeSuggester

tool = Tool(
    name="analyze_note",
    description="""Analyzes clinical documentation and returns:
    - findings: Key clinical findings
    - missing_elements: Documentation gaps
    - recommended_codes: ICD-10/CPT suggestions
    - entities: Extracted clinical entities (diagnoses, meds, labs, etc.)
    - documentation_risks: Compliance and coding risks""",
    input_schema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "The clinical note text to analyze"
            }
        },
        "required": ["note_text"]
    }
)

async def handler(note_text: str) -> dict:
    gap_detector = DocumentationGapDetector()
    entity_extractor = ClinicalEntityExtractor()
    code_suggester = CodeSuggester()

    gaps = await gap_detector.detect_gaps(note_text)
    entities = await entity_extractor.extract(note_text)
    codes = await code_suggester.suggest_from_text(note_text)

    return {
        "findings": gaps.findings,
        "missing_elements": [g.dict() for g in gaps.gaps],
        "recommended_codes": [c.dict() for c in codes.suggestions],
        "documentation_risks": gaps.risks,
        "entities": entities.dict()
    }

tool.handler = handler
```

**tools/generate_query.py**
```python
tool = Tool(
    name="generate_query",
    description="""Creates physician-facing documentation queries to clarify
    or improve note completeness. Returns non-leading, clinically appropriate
    queries for CDI specialists to send to providers.""",
    input_schema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "The clinical note with documentation gaps"
            },
            "gap_type": {
                "type": "string",
                "description": "Specific gap type to address (optional)",
                "enum": ["specificity", "acuity", "comorbidity", "medical_necessity"]
            }
        },
        "required": ["note_text"]
    }
)
```

**tools/search_icd10.py**
```python
tool = Tool(
    name="search_icd10",
    description="""Searches ICD-10 diagnosis codes using semantic similarity.
    Understands clinical language and finds relevant codes even with
    non-standard terminology.""",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (clinical term, condition, or code)"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
)
```

**tools/search_cpt.py**
```python
tool = Tool(
    name="search_cpt",
    description="""Searches CPT/HCPCS procedure codes using semantic similarity.
    Finds relevant procedure codes based on clinical descriptions.""",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (procedure description or code)"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
)
```

**tools/calculate_fees.py** (NEW)
```python
tool = Tool(
    name="calculate_fees",
    description="""Calculates Medicare reimbursement for procedure codes.
    Uses CMS Medicare Physician Fee Schedule with locality-specific rates.
    Returns pricing breakdown including RVUs and conversion factors.""",
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "CPT or HCPCS code"
            },
            "zip_code": {
                "type": "string",
                "description": "ZIP code for locality-specific pricing"
            },
            "year": {
                "type": "integer",
                "description": "Fee schedule year",
                "default": 2025
            },
            "facility": {
                "type": "boolean",
                "description": "Whether facility or non-facility rate",
                "default": False
            }
        },
        "required": ["code", "zip_code"]
    }
)
```

**tools/optimize_revenue.py**
```python
tool = Tool(
    name="optimize_revenue",
    description="""Analyzes clinical documentation for revenue optimization.
    Identifies under-coded conditions, severity opportunities, HCC opportunities,
    and E/M coding recommendations. Does not promote upcoding - focuses on
    accurate capture of documented conditions.""",
    input_schema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "Clinical note to analyze"
            },
            "include_em_coding": {
                "type": "boolean",
                "description": "Include E/M coding analysis",
                "default": True
            },
            "include_hcc": {
                "type": "boolean",
                "description": "Include HCC risk adjustment analysis",
                "default": True
            }
        },
        "required": ["note_text"]
    }
)
```

**tools/evaluate_hedis.py**
```python
tool = Tool(
    name="evaluate_hedis",
    description="""Evaluates clinical documentation against HEDIS quality measures.
    Supports 19 measures including CBP, CDC, BCS, COL, BMI, DEP, and more.
    Returns compliance status and gaps for each applicable measure.""",
    input_schema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "Clinical note to evaluate"
            },
            "patient_age": {
                "type": "integer",
                "description": "Patient age in years"
            },
            "patient_gender": {
                "type": "string",
                "description": "Patient gender (male/female)",
                "enum": ["male", "female"]
            },
            "icd10_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Known ICD-10 codes for the patient (optional)"
            }
        },
        "required": ["note_text", "patient_age", "patient_gender"]
    }
)
```

**tools/extract_entities.py**
```python
tool = Tool(
    name="extract_entities",
    description="""Extracts medical entities from clinical text including:
    - diagnoses: Medical conditions and diseases
    - symptoms: Patient-reported or observed symptoms
    - medications: Current and historical medications
    - labs: Laboratory test results
    - vitals: Vital sign measurements
    - procedures: Performed or planned procedures
    - social_determinants: Social factors affecting health""",
    input_schema={
        "type": "object",
        "properties": {
            "note_text": {
                "type": "string",
                "description": "Clinical text to extract entities from"
            }
        },
        "required": ["note_text"]
    }
)
```

#### 6.3 MCP Configuration

**mcp_config.json** (for Claude Desktop)
```json
{
  "mcpServers": {
    "nuvii-cdi": {
      "command": "python",
      "args": ["-m", "adapters.mcp.server"],
      "cwd": "/path/to/nuvii-cdi-agent/backend",
      "env": {
        "DATABASE_URL": "postgresql://...",
        "ANTHROPIC_API_KEY": "..."
      }
    }
  }
}
```

### Deliverables
- [ ] MCP server implementation complete
- [ ] All 8 tools implemented and tested
- [ ] JSON schemas validate correctly
- [ ] Works with Claude Desktop
- [ ] Docker container for MCP server

---

## Phase 7: Knowledge Base Migration

### Objective
Migrate CDI Agent knowledge bases to PostgreSQL.

### Tasks

#### 7.1 Data Migration Scripts

**scripts/load_cdi_guidelines.py**
```python
"""
Load CDI guidelines from PDF documents into PostgreSQL.

Sources:
- CDI Agent's cdi_documents/ folder
- Processed PDF text with embeddings
"""

async def load_guidelines():
    # 1. Load PDF documents
    # 2. Chunk into guideline segments
    # 3. Generate embeddings (MedCPT 768-dim)
    # 4. Insert into cdi_guidelines table
```

**scripts/load_investigation_protocols.py**
```python
"""
Load investigation protocols from CDI Agent JSON files.

Source: CDIAgent/knowledge_base/investigations/*.json
"""

async def load_protocols():
    # 1. Load JSON files for each condition
    # 2. Parse protocol structure
    # 3. Generate embeddings for each test description
    # 4. Insert into investigation_protocols table
```

**scripts/load_em_codes.py**
```python
"""
Load E/M code reference data.

Source: CDIAgent/knowledge_base/em_codes/em_codes.json
"""

async def load_em_codes():
    # 1. Load E/M code definitions
    # 2. Parse requirements and reimbursement
    # 3. Insert into em_codes table
```

**scripts/migrate_cdi_agent_data.py**
```python
"""
Master migration script - runs all data migrations.
"""

async def migrate_all():
    await load_cdi_guidelines()
    await load_investigation_protocols()
    await load_em_codes()
    await generate_all_embeddings()
    await verify_migration()
```

#### 7.2 Data Files to Migrate

| Source | Target Table | Records (est.) |
|--------|--------------|----------------|
| `CDIAgent/cdi_documents/*.pdf` | `cdi_guidelines` | ~5,000 |
| `CDIAgent/knowledge_base/investigations/*.json` | `investigation_protocols` | ~4,500 |
| `CDIAgent/knowledge_base/em_codes/em_codes.json` | `em_codes` | ~100 |

#### 7.3 Embedding Generation

Generate 768-dimensional MedCPT embeddings for:
- CDI guideline content
- Investigation protocol descriptions
- Search will use same embedding model as ICD-10/CPT

### Deliverables
- [ ] All migration scripts created
- [ ] Data successfully migrated
- [ ] Embeddings generated for all new content
- [ ] Verification queries pass
- [ ] Search performance validated

---

## Phase 8: Frontend Updates

### Objective
Update Next.js frontend to work with new API structure.

### Tasks

#### 8.1 Update API Client

**lib/api.ts** - Update endpoints
```typescript
// Code Search
export const searchICD10 = (params: CodeSearchParams) =>
  api.get('/api/v1/codes/icd10/hybrid', { params });

export const searchProcedures = (params: CodeSearchParams) =>
  api.get('/api/v1/codes/procedure/hybrid', { params });

export const suggestCodes = (text: string) =>
  api.post('/api/v1/codes/suggest', { text });

// CDI Analysis (NEW)
export const analyzeNote = (note: string) =>
  api.post('/api/v1/cdi/analyze', { clinical_note: note });

export const generateCDIQuery = (note: string, gapType?: string) =>
  api.post('/api/v1/cdi/generate-query', { clinical_note: note, gap_type: gapType });

export const getCDIQueryHistory = (params: PaginationParams) =>
  api.get('/api/v1/cdi/query-history', { params });

// Revenue (NEW)
export const analyzeRevenue = (request: RevenueRequest) =>
  api.post('/api/v1/revenue/analyze', request);

export const getEMCoding = (note: string, setting: string) =>
  api.post('/api/v1/revenue/em-coding', { clinical_note: note, setting });

// Quality (NEW)
export const evaluateHEDIS = (request: HEDISRequest) =>
  api.post('/api/v1/quality/hedis', request);

// Fee Schedule
export const getPrice = (code: string, zipCode: string) =>
  api.get('/api/v1/fees/price', { params: { code, zip_code: zipCode } });

export const analyzeContract = (request: ContractRequest) =>
  api.post('/api/v1/fees/contract-analysis', request);
```

#### 8.2 New Dashboard Pages

**app/dashboard/cdi/** - CDI Analysis Pages
```
app/dashboard/cdi/
├── page.tsx              # CDI Dashboard overview
├── analyze/
│   └── page.tsx          # Note analysis tool
├── query-generator/
│   └── page.tsx          # CDI query generator
├── history/
│   └── page.tsx          # Query history
└── guidelines/
    └── page.tsx          # Browse CDI guidelines
```

**app/dashboard/revenue/** - Revenue Pages
```
app/dashboard/revenue/
├── page.tsx              # Revenue dashboard
├── analyze/
│   └── page.tsx          # Revenue analysis tool
├── em-coding/
│   └── page.tsx          # E/M coding tool
└── hcc/
    └── page.tsx          # HCC evaluation
```

**app/dashboard/quality/** - Quality Pages
```
app/dashboard/quality/
├── page.tsx              # Quality dashboard
├── hedis/
│   └── page.tsx          # HEDIS evaluation tool
└── history/
    └── page.tsx          # Evaluation history
```

#### 8.3 Update Navigation

**components/DashboardNav.tsx**
```typescript
const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Code Search', href: '/dashboard/playground', icon: SearchIcon },
  { name: 'CDI Analysis', href: '/dashboard/cdi', icon: DocumentTextIcon },
  { name: 'Revenue', href: '/dashboard/revenue', icon: CurrencyDollarIcon },
  { name: 'Quality', href: '/dashboard/quality', icon: ChartBarIcon },
  { name: 'Fee Schedule', href: '/dashboard/fee-schedule', icon: CalculatorIcon },
  { name: 'API Keys', href: '/dashboard/api-keys', icon: KeyIcon },
  { name: 'Usage', href: '/dashboard/usage', icon: ChartPieIcon },
  { name: 'Billing', href: '/dashboard/billing', icon: CreditCardIcon },
  { name: 'Docs', href: '/dashboard/docs', icon: BookOpenIcon },
];
```

#### 8.4 TypeScript Types

**types/cdi.ts**
```typescript
export interface NoteAnalysisResult {
  findings: string[];
  documentation_gaps: DocumentationGap[];
  recommended_codes: CodeSuggestion[];
  entities: ExtractedEntities;
  confidence_score: number;
}

export interface DocumentationGap {
  type: 'specificity' | 'acuity' | 'comorbidity' | 'medical_necessity';
  description: string;
  severity: 'high' | 'medium' | 'low';
  suggestion: string;
}

export interface CDIQueryResult {
  query: string;
  source_documents: string[];
  validation: ValidationResult;
  confidence: number;
}
```

**types/revenue.ts**
```typescript
export interface RevenueAnalysisResult {
  condition: string;
  severity: string;
  test_analysis: TestAnalysis;
  revenue_analysis: RevenueBreakdown;
  em_coding?: EMCodingResult;
  drg_optimization?: DRGResult;
  total_opportunity: number;
}

export interface EMCodingResult {
  recommended_code: string;
  current_level: string;
  potential_upgrade?: string;
  documentation_gaps: string[];
  mdm_analysis: MDMAnalysis;
}
```

### Deliverables
- [ ] API client updated with all new endpoints
- [ ] New dashboard pages created
- [ ] Navigation updated
- [ ] TypeScript types defined
- [ ] All pages functional and tested

---

## Phase 9: Testing & Validation

### Objective
Comprehensive testing to ensure quality and correctness.

### Tasks

#### 9.1 Test Structure

```
tests/
├── domain/
│   ├── test_coding_helper.py
│   ├── test_documentation_gaps.py
│   ├── test_query_generation.py
│   ├── test_revenue_optimization.py
│   ├── test_hedis_evaluation.py
│   ├── test_entity_extraction.py
│   ├── test_semantic_search.py
│   └── test_fee_schedule.py
│
├── adapters/
│   ├── api/
│   │   ├── test_codes_routes.py
│   │   ├── test_cdi_routes.py
│   │   ├── test_revenue_routes.py
│   │   ├── test_quality_routes.py
│   │   └── test_fees_routes.py
│   │
│   └── mcp/
│       ├── test_mcp_server.py
│       └── test_mcp_tools.py
│
├── infrastructure/
│   ├── test_database.py
│   ├── test_repositories.py
│   └── test_llm_engines.py
│
├── integration/
│   ├── test_end_to_end.py
│   ├── test_cdi_workflow.py
│   └── test_revenue_workflow.py
│
└── fixtures/
    ├── clinical_notes.py
    ├── expected_results.py
    └── mock_data.py
```

#### 9.2 Test Cases

**Domain Tests**
- CDI query generation produces non-leading questions
- Documentation gap detection finds known gaps
- HEDIS measures evaluate correctly against test cases
- E/M coding matches expected levels
- Fee calculations match CMS published rates

**API Tests**
- All endpoints return correct status codes
- Input validation works correctly
- Authentication required where expected
- Rate limiting functions properly

**MCP Tests**
- All tools register correctly
- Tool schemas validate inputs
- Tool responses match expected format
- Error handling works properly

**Integration Tests**
- End-to-end CDI workflow
- Revenue analysis workflow
- HEDIS evaluation workflow
- Search functionality

#### 9.3 Performance Benchmarks

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| ICD-10 Search | < 100ms | Semantic search |
| CDI Query Generation | < 5s | LLM dependent |
| Note Analysis | < 6s | Full analysis |
| Entity Extraction | < 3s | |
| Fee Calculation | < 50ms | Database lookup |
| HEDIS Evaluation | < 5s | With query generation |

### Deliverables
- [ ] All test files created
- [ ] >80% code coverage
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] CI/CD pipeline updated

---

## Phase 10: Documentation & Deployment

### Objective
Complete documentation and prepare for deployment.

### Tasks

#### 10.1 Documentation

**docs/architecture.md**
- System architecture diagram
- Component descriptions
- Data flow diagrams

**docs/api/**
- OpenAPI specification (auto-generated)
- API usage examples
- Authentication guide

**docs/mcp/**
- MCP server setup guide
- Tool documentation
- Claude Desktop configuration

**README.md**
- Updated quick start
- Feature overview
- Development setup

#### 10.2 Docker Updates

**Dockerfile** (updated)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

# Default to API server
CMD ["uvicorn", "adapters.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml** (updated)
```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: nuvii_cdi
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/nuvii_cdi
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: uvicorn adapters.api.main:app --host 0.0.0.0 --port 8000 --reload

  mcp:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/nuvii_cdi
    depends_on:
      - postgres
    command: python -m adapters.mcp.server
    stdin_open: true
    tty: true

volumes:
  postgres_data:
```

#### 10.3 CI/CD Updates

- Update GitHub Actions workflows
- Add test coverage requirements
- Add deployment stages

### Deliverables
- [ ] Architecture documentation complete
- [ ] API documentation updated
- [ ] MCP setup guide created
- [ ] Docker configurations updated
- [ ] CI/CD pipeline functional

---

## Implementation Timeline

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | **Phase 1** | Directory structure, file moves, imports updated |
| 2 | **Phase 2** | Infrastructure layer complete (DB, LLM, Config) |
| 3 | **Phase 4** | Database schema extensions, migrations |
| 4 | **Phase 3.1-3.2** | Semantic search, coding helper, documentation gaps |
| 5 | **Phase 3.3-3.4** | Query generation, revenue optimization |
| 6 | **Phase 3.5-3.7** | HEDIS, entity extraction, fee schedule |
| 7 | **Phase 5** | REST API endpoints complete |
| 7 | **Phase 7** | Knowledge base migration |
| 8 | **Phase 6** | MCP server implementation |
| 9 | **Phase 8** | Frontend updates |
| 10 | **Phase 9** | Testing & validation |
| 11 | **Phase 10** | Documentation & deployment |

**Total Estimated Duration: 11 weeks**

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Vector Database** | PostgreSQL + pgvector | Already in production, no new dependencies |
| **Remove ChromaDB** | Yes | Simplify stack, PostgreSQL handles all vector ops |
| **Primary LLM** | Claude API (Anthropic) | Already integrated, excellent clinical performance |
| **LLM Fallback** | OpenAI GPT-4 | Widely available, good fallback option |
| **Local LLM** | Optional Mistral | For air-gapped/VPC deployments |
| **Embedding Model** | MedCPT (768-dim) | Clinically trained, already in use |
| **MCP Transport** | STDIO JSON-RPC | Standard MCP protocol |
| **Frontend Framework** | Keep Next.js 14 | Already in production, no need to change |
| **API Framework** | Keep FastAPI | Already in production, excellent async support |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM latency for CDI queries | Medium | Medium | Implement caching, async processing |
| Data migration data loss | Low | High | Backup before migration, verification scripts |
| Breaking frontend | Medium | Medium | Comprehensive API testing, gradual rollout |
| MCP compatibility issues | Medium | Low | Test with multiple MCP clients |
| Performance degradation | Low | Medium | Benchmarking at each phase |
| Embedding model changes | Low | Medium | Version embeddings, re-generate if needed |

---

## Success Criteria

1. **All existing functionality works** after refactoring
2. **CDI query generation** produces quality comparable to CDI Agent
3. **HEDIS evaluation** covers all 19 measures
4. **MCP tools** work in Claude Desktop and VS Code
5. **API response times** meet performance targets
6. **Test coverage** exceeds 80%
7. **Documentation** is complete and accurate

---

## Appendix A: Removed Dependencies

The following dependencies from CDI Agent will NOT be used:

| Dependency | Reason |
|------------|--------|
| ChromaDB | Replaced by PostgreSQL + pgvector |
| Mistral-7B (local) | Replaced by Claude API (optional local support) |
| all-MiniLM-L6-v2 | Replaced by MedCPT (768-dim) |
| BM25Retriever | Replaced by PostgreSQL TSVECTOR + trigram |
| QLoRA/BitsAndBytes | Not needed (using API-based LLM) |

---

## Appendix B: New Dependencies

| Dependency | Purpose |
|------------|---------|
| mcp | MCP server framework |
| anthropic | Claude API client (already present) |
| openai | GPT-4 fallback (optional) |

---

**Document Version:** 1.0
**Last Updated:** 2025-11-27
**Status:** Ready for Review
