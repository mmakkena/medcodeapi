# Product Requirements Document: CMS Fee Schedule Explorer & Contract Analyzer

| **Project Name** | Fee Schedule Explorer (Project Code: *ClearRate*) |
| :--- | :--- |
| **Version** | 1.0 (MVP Draft) |
| **Status** | Planning |
| **Target Audience** | Practice Managers, Medical Billers, RCM Consultants |
| **Core Value** | Transform complex government pricing data into actionable negotiation leverage. |

---

## 1. Problem Statement
**Context:**
The CMS (Medicare) Physician Fee Schedule (MPFS) is the baseline for 90% of US healthcare pricing. However, the data is published in hostile formats (massive CSVs, complex PDFs) and varies by strict geographic localities (GPCI).

**The Pain:**
1.  **Accessibility:** Looking up a specific reimbursement rate for a specific ZIP code involves navigating complex CMS websites or downloading 50MB+ files.
2.  **Comparison:** Clinics cannot easily compare their private payer contracts (e.g., Aetna, UHC) against Medicare baselines to see if they are being underpaid.
3.  **Historical Data:** Tracking reimbursement cuts/hikes year-over-year is manual and prone to error.

**The Solution:**
A hosted, fast, search-first SaaS that normalizes CMS data, maps ZIP codes to localities automatically, and allows users to upload private fee schedules for instant "gap analysis."

---

## 2. User Personas

### A. Betty the Biller (Daily User)
* **Goal:** Quickly check the Medicare allowable rate for a specific CPT code to ensure the claim is submitted correctly or to collect the right co-pay.
* **Frustration:** CMS.gov is slow; she hates downloading spreadsheets.
* **Needs:** Lightning-fast search bar. "Type '99213' -> see price."

### B. Marcus the Manager (Buyer/Admin)
* **Goal:** Negotiate better rates with private payers during contract renewal.
* **Frustration:** He suspects Blue Cross is paying less than Medicare for ultrasounds but lacks the data to prove it easily.
* **Needs:** Bulk upload tool, comparison visualization, export to Excel for meetings.

---

## 3. Functional Requirements

### 3.1. Core Data Engine (The Backend)
| ID | Feature | Description | Priority |
| :--- | :--- | :--- | :--- |
| **BE-01** | **CMS Ingestion Pipeline** | Automated scripts to ingest CMS MPFS (Physician Fee Schedule) CSVs. Must handle quarterly updates. | P0 (Critical) |
| **BE-02** | **Geo-Mapping Engine** | Map US ZIP Codes to CMS "Localities" (GPCI). *Example: ZIP 02139 maps to '0110101 Metropolitan Boston'.* | P0 |
| **BE-03** | **RVU Calculation** | System must calculate price dynamically: `(Work RVU * Work GPCI) + (PE RVU * PE GPCI) + (MP RVU * MP GPCI) * Conversion Factor`. | P0 |
| **BE-04** | **Modifier Logic** | Handle price adjustments for modifiers: TC (Technical Component), 26 (Professional), 53 (Assistant Surgeon). | P1 |

### 3.2. User Interface (The Frontend)
| ID | Feature | Description | Priority |
| :--- | :--- | :--- | :--- |
| **FE-01** | **Universal Search** | ElasticSearch-style bar. Accepts CPT Codes (e.g., "99213") or Keywords (e.g., "Office Visit"). | P0 |
| **FE-02** | **Context Switcher** | Dropdowns for **Year** (2024, 2025) and **Location** (Input ZIP code -> Auto-select Locality). | P0 |
| **FE-03** | **The "Card" View** | Display CPT details cleanly: Code, Description, Non-Facility Price, Facility Price, and Global Days. | P0 |
| **FE-04** | **Bulk List Creator** | Users can "star" or save codes into lists (e.g., "Cardiology Top 20"). | P1 |

### 3.3. The "Contract Analyzer" (The Monetization Feature)
| ID | Feature | Description | Priority |
| :--- | :--- | :--- | :--- |
| **AN-01** | **CSV Upload** | User uploads a 2-column CSV: `CPT Code`, `Current Price`. | P1 |
| **AN-02** | **The "Red Flag" Report** | System matches uploaded codes against CMS baseline. Highlights any code where `User Price < CMS Price` in red. | P1 |
| **AN-03** | **Revenue Impact** | User enters volume (e.g., "We do 500 of these a year"). System calculates total potential revenue loss. | P2 |

---

## 4. Non-Functional Requirements

* **Performance:** Search results must load in **< 200ms**. This is a utility tool; speed is the primary feature.
* **Accuracy:** Data must match CMS files to the penny. Discrepancies destroy trust.
* **Security:**
    * Data Encryption at Rest (AES-256).
    * While Fee Schedules are technically *not* PHI (Patient Health Info), they are **Confidential Business Information**. Strict access controls are required.
* **Mobile Responsive:** "Betty the Biller" might check a code on her phone while at the front desk.

---

## 5. Data Strategy & Sources

* **Primary Source:** [CMS Physician Fee Schedule (PFS) Relative Value Files](https://www.cms.gov/medicare/physician-fee-schedule/search).
* **Update Cadence:**
    * **January 1:** Major annual update (new RVUs and Conversion Factor).
    * **Quarterly:** Minor updates (new codes, corrections).
* **Normalization Challenge:** CMS data often splits into "A" files (RVUs) and "B" files (GPCI). The ETL pipeline must merge these based on Year/Quarter.

---

## 6. Proposed Tech Stack (MVP)

* **Frontend:** Use existing one
* **UI Framework:** use existing CSS
* **Backend:** use existing one
* **Database:** use existing DB
* **Search:** Postgres Full Text Search (sufficient for MVP) or MeiliSearch.

---

## 7. Roadmap / Phasing

### Phase 1: The "Magnet" (Free Tool)
* Publicly accessible.
* Search CMS rates by CPT and ZIP code.
* No login required.
* *Goal: SEO dominance and traffic.*

### Phase 2: The "Pro" (Paid - $49-$99/mo)
* User Accounts.
* Save "Favorite Lists."
* **Contract Analyzer** (Upload private fee schedules).
* Export to Excel/PDF.

### Phase 3: The API (Developer Tier)
* Rest API access for other HealthTech apps.
* `GET /v1/price?code=99213&zip=10001`
* Metered billing.

---

## 8. Success Metrics

1.  **Search Latency:** Avg search < 200ms.
2.  **Conversion:** 5% of "Free Search" users sign up for a trial of "Pro" features.
3.  **Data Integrity:** Zero user reports of incorrect pricing vs. CMS.gov.
The Solution: Hybrid Search (The "Best Practice")You need a system that runs two searches in parallel and fuses the results (often called RRF - Reciprocal Rank Fusion).3The "Precision" Layer (BM25 / Keyword): Matches exact CPT numbers (99213) or exact phrases ("Office Visit"). This acts as a hard filter.The "Concept" Layer (Vector Embeddings): Catches the synonyms and intent ("Heart attack" $\rightarrow$ Myocardial Infarction).4. Technical Implementation (How to build it)Don't train your own model from scratch. Use open-source models pre-trained on medical texts (PubMed/MIMIC-III).4Recommended Models (Hugging Face):medicalai/ClinicalBERT: Excellent for understanding clinical notes and jargon.5cambridgeltl/BioRedditBERT: Surprisingly good at layman terms (how patients describe symptoms).pritamdeka/S-PubMedBert-MS-MARCO: Optimized for search/retrieval tasks specifically.Architecture for your MVP:Database: Use Postgres (pgvector). You don't need a separate Pinecone instance for this scale. It keeps your stack simple.Ingestion: When you ingest the CMS CSV, run the descriptions through ClinicalBERT to generate vectors. Store them in a embedding column.Query:SQL-- Pseudo-code for Hybrid Search

 prioritize "Keyword Matches" in your ranking algorithm.If a user types a specific CPT code (e.g., 99213), the system should never be "smart" and show them 99214. It should show them exactly what they typed. Only engage the semantic engine when the query looks like natural language (e.g., "knee injection").