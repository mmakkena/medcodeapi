📄 CDI Agent MCP Server — Requirements Specification

Version: 1.0
Author: Murali / Nuvii
Date: 2025-01-01
Document Type: Technical Requirements (MCP Server)

1. Overview

The CDI Agent MCP Server provides structured tool interfaces (via Model Context Protocol) for performing automated Clinical Documentation Integrity (CDI) tasks, including:

Clinical note analysis

Missing documentation detection

ICD-10/CPT semantic search

Query generation

Revenue optimization support

Entity extraction

The MCP server allows LLM clients (e.g., Claude Desktop, VS Code, internal agent UIs) to interact with local CDI logic running inside customer environments or developer machines.

This document covers only the MCP server interface, not API or backend domain logic.

2. Goals & Non-Goals
2.1 Goals

Provide structured MCP tools for CDI workflows

Expose CDI functionality to LLM-based agents

Enable local/on-prem deployments inside customer environments

Allow zero-PHI egress by keeping processing local

Reuse the same domain logic used by the API service (via shared module)

Offer consistent JSON schemas across tools

Be compatible with major MCP clients (Claude Desktop, VS Code agent extensions)

2.2 Non-Goals

Implement business logic for CDI (handled by domain layer)

Provide a REST API (covered in separate API spec)

Handle authentication (MCP local mode does not require it)

Serve UI or dashboards

Manage billing/licensing (enterprise function, outside MCP scope)

3. Architecture
3.1 High-Level Components
[MCP Client] ←→ [MCP Server Adapter Layer] ←→ [Shared CDI Domain Layer]
                                           ←→ [Local/Remote LLM]
                                           ←→ [Postgres Vector DB (ICD/CPT)]

3.2 MCP Server Responsibilities

Define MCP capabilities

Register tools

Provide JSON Schema for each tool’s input/output

Transform MCP tool requests into domain-layer function calls

Stream final results to the MCP client

Log structured tool invocation events

4. MCP Tools & Capabilities

The MCP server must expose the following tools:

4.1 analyze_note

Analyzes clinical documentation and returns:

findings

missing documentation

clinical entities

HCC implications

coding opportunities

Input Schema

{
  "type": "object",
  "properties": {
    "note_text": { "type": "string" }
  },
  "required": ["note_text"]
}


Output Schema

{
  "type": "object",
  "properties": {
    "findings": { "type": "array", "items": { "type": "string" } },
    "missing_elements": { "type": "array", "items": { "type": "string" } },
    "recommended_codes": { "type": "array" },
    "documentation_risks": { "type": "array" },
    "entities": { "type": "object" }
  }
}

4.2 generate_query

Creates physician-facing documentation queries to clarify or improve note completeness.

Input

{ "note_text": "string" }


Output

{
  "queries": ["string"]
}

4.3 optimize_revenue

Analyzes documentation and suggests ways to ensure accurate coding aligned with clinical severity and HCC logic.

Input

{
  "note_text": "string",
  "diagnosis_list": { "type": "array", "items": { "type": "string" } }
}


Output

{
  "under_coded_conditions": ["string"],
  "severity_opportunities": ["string"],
  "hcc_opportunities": ["string"]
}

4.4 semantic_search_icd10

Searches ICD-10 codes using Postgres vector embeddings.

Input

{
  "query": "string",
  "top_k": { "type": "number", "default": 5 }
}


Output

{
  "results": [
    {
      "code": "string",
      "description": "string",
      "score": "number"
    }
  ]
}

4.5 semantic_search_cpt

(Optional) CPT description search.

4.6 extract_entities

Extracts medical entities:

diagnoses

symptoms

labs

meds

procedures

social determinants

Input

{ "note_text": "string" }


Output

{
  "diagnoses": ["string"],
  "symptoms": ["string"],
  "medications": ["string"],
  "labs": ["string"],
  "procedures": ["string"]
}

5. Deployment Requirements
5.1 Supported Deployment Targets

Customer VPC (AWS/GCP/Azure)

Customer on-prem data center

Hospital secure environment

Air-gapped systems

Developer local machine

5.2 Runtime Requirements

Node.js ≥ 20.x or Python ≥ 3.10

Ability to connect to domain layer via shared module

Local logging

JSON-RPC over STDIO for MCP compatibility

5.3 Container Requirements (If Dockerized)

Alpine, Debian, or Distroless image

Must run without outbound internet (if local LLM is used)

Optional GPU support (NVIDIA CUDA)

6. Security & Compliance
6.1 PHI Boundary Rules

No PHI leaves customer environment

No logs contain PHI unless customer permits

All processing occurs in their VPC/on-prem

Must support offline mode (no external APIs)

6.2 Auditability

Log tool invocation events only

No raw note text stored unless enabled

6.3 Optional: Model Execution

Customers may choose:

Local LLM (Llama 3, Mistral, Nous Hermes)

Customer’s cloud LLM endpoint

Encrypted tunnel to Nuvii LLM if covered by BAA

7. Performance Requirements
7.1 Latency Targets

Analyze Note: ≤ 2–6 seconds (LLM dependent)

ICD Search: ≤ 50 ms (Postgres vector)

Entity Extraction: ≤ 1–3 seconds

Query Generation: ≤ 3–5 seconds

7.2 Throughput

Single-threaded acceptable (MCP is interactive)

Must support concurrent tool calls

8. Logging Requirements

Log JSON events for:

tool name

execution duration

errors

warnings

system health

Never log full PHI unless PHI_LOGGING=true.

9. Configuration Requirements
Environment Variables
Variable	Description
CDI_MODEL_PATH	Local or remote LLM
PG_HOST	Postgres vector DB
PG_DB	Database name
PG_USER	DB user
PG_PASSWORD	DB password
LOG_LEVEL	debug/info/warn/error
10. Error Handling Requirements

Server must return structured MCP errors:

{
  "error": {
    "type": "tool_error",
    "message": "ICD search database unavailable"
  }
}

11. Tool Registration Example (Reference)
server.tool("analyze_note", async ({ note_text }) => {
  return await domain.analyzeNote(note_text);
});

server.tool("generate_query", async ({ note_text }) => {
  return await domain.generateQuery(note_text);
});

server.tool("optimize_revenue", async ({ note_text, diagnosis_list }) => {
  return await domain.optimizeRevenue(note_text, diagnosis_list);
});

server.tool("semantic_search_icd10", async ({ query, top_k }) => {
  return await domain.searchICD10(query, top_k);
});

12. Acceptance Criteria

MCP server loads without errors

All tools appear in Claude Desktop / MCP client

Each tool validates input schema

Each tool returns valid JSON matching output schema

No PHI egress

Deployment works in offline mode

Reuses shared domain logic implementation

Can be packaged as Docker container

13. Future Enhancements (Optional)

Patient timeline summarization

Prior authorization agent

Real-time audit mode

CPT/HCPCS search

Risk score calculator tool

Streaming responses

Multi-model routing

