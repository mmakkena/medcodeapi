I want to refactor the current project code in anticipation of the following 2 major changes

1) 
    I have another project for clinical documentation gaps, hedis evaluation, CDI query generation and revenue optimization in ../CDIAgent project and is documented in ../CDIAgent/PROJECT_DOCUMENTATION.md file
    I want to bring those features into this current project and use the same techonologies and db used in this project. combine the backend code with API support.

2) Add MCP server capabilities under docuemnted in docs/requirements/mcpserver.md


Here is one idea to structure the project. We do not need to go exactly like this. we can adapt this structure based on our code and functionality.




nuvii-cdi-agent/
│
├── domain/                        # Core CDI logic (shared across everything)
│   ├── coding_helper/
│   ├── documentation_gaps/
│   ├── query_generation/
│   ├── revenue_optimization/
│   ├── entity_extraction/
│   ├── semantic_search/
│   ├── common/                    # scoring, heuristics, utilities
│   └── __init__.py
│
├── adapters/                      # Everything that consumes the domain layer
│   ├── api/                       # REST API (FastAPI/Express)
│   │   ├── routes/
│   │   ├── controllers/
│   │   └── main.py
│   │
│   ├── mcp/                       # MCP Server (Claude, VS Code, etc)
│   │   ├── tools/
│   │   ├── schemas/
│   │   └── server.py
│   │
│   ├── slack/                     # Slack bot integration
│   │   ├── handlers/
│   │   └── bot.py
│   │
│   ├── teams/                     # Teams integration
│   │   └── bot.py
│   │
│   └── cli/                       # Command-line tool (optional)
│       └── cli.py
│
├── infrastructure/
│   ├── db/
│   │   ├── postgres.py            # ICD/CPT vector store
│   │   └── migrations/
│   │
│   ├── llm/
│   │   ├── openai_engine.py
│   │   ├── anthropic_engine.py
│   │   ├── mistral_engine.py
│   │   └── local_engine.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── logging/
│       └── log.py
│
├── tests/
│   ├── domain/
│   ├── api/
│   ├── mcp/
│   └── slack/
│
├── docs/
│   ├── requirements/
│   │   └── mcp_requirements.md
│   │
│   ├── api/
│   │   └── openapi.yaml
│   │
│   └── architecture.md
│
├── scripts/
│   └── load_embeddings.py
│
├── Dockerfile
├── docker-compose.yaml
├── README.md
└── pyproject.toml / package.json

🔥 How Each Feature Fits Into the Structure
1️⃣ Medical Coding Helper

Path: domain/coding_helper/

Includes:

Code suggestions

CPT/ICD comparison

Diagnosis completeness

Code validation

Reuses semantic search + LLM inference.

2️⃣ Clinical Documentation Gaps

Path: domain/documentation_gaps/

Includes:

Missing specificity

Missing acuity

Missing co-morbidities

Required documentation based on diagnosis

Medical necessity gaps

This powers both MCP + API responses.

3️⃣ CDI Query Generation

Path: domain/query_generation/

Includes:

Clarification queries

Provider-friendly phrasing

Regulatory-compliant format

Multiple query styles (open-ended, yes/no, documentation-based)

Your MCP and Slack bot tools call the same functions.

4️⃣ Revenue Optimization

Path: domain/revenue_optimization/

Includes:

HCC model logic (V24, V28)

Risk adjustment opportunities

Under-coded conditions

Suggested documentation that increases accuracy

Value-based care scoring

This module feeds:

CDI teams (MCP)

Coders (Slack/Teams)

External customers (API)

5️⃣ Semantic Search

Path: domain/semantic_search/

Uses vector DB:

ICD-10 embeddings

CPT embeddings

paraphrased descriptions

fuzzy matching

Infrastructure layer (postgres.py) implements the DB engine.

6️⃣ MCP Server

Path: adapters/mcp/

Minimal glue code:

result = domain.coding_helper.suggest_codes(note)

7️⃣ REST API Layer

Path: adapters/api/

REST → domain functions.

8️⃣ Slack/Teams Bots

Path: adapters/slack/, adapters/teams/

Examples:

result = domain.query_generation.generate(note)

🎯 Why This Structure Works
✔ Single source of truth

Domain layer holds all CDI logic — used by API + MCP + Slack.

✔ Easy to deploy inside customer VPC

Because all adapters are lightweight.

✔ Extensible

You can add:

FHIR integration

Epic App Orchard connector

Prior authorization agent

Pre-bill audit agent
with no rewrites.

✔ Perfect DACI separation

Domain = Intelligence

Adapters = Interface

Infrastructure = Tools + DB + LLM

MCP = Interoperability