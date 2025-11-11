# AI-Powered Clinical Note Coding

## Overview

The `/api/v1/clinical-coding` endpoint uses AI to automatically extract diagnoses and procedures from free-text clinical notes and suggest appropriate ICD-10 and CPT/HCPCS codes.

## How It Works

1. **LLM Entity Extraction**: Claude 3.5 Sonnet analyzes the clinical note to extract:
   - Chief complaint
   - Primary diagnoses
   - Secondary diagnoses (comorbidities, history)
   - Procedures performed
   - Clinical context

2. **Semantic Code Search**: For each extracted entity, the system searches:
   - ICD-10-CM codes for diagnoses using MedCPT embeddings
   - CPT/HCPCS codes for procedures using MedCPT embeddings
   - Returns top matches with similarity scores

3. **AI Reasoning & Ranking**: Results are:
   - Categorized (primary dx, secondary dx, procedures)
   - Ranked by confidence scores
   - Enriched with AI explanations

## API Endpoint

```
POST /api/v1/clinical-coding
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Request Schema

```json
{
  "clinical_note": "Full clinical documentation text (min 50 characters)",
  "max_codes_per_type": 5,
  "include_explanations": true,
  "version_year": 2025
}
```

### Response Schema

```json
{
  "clinical_note_summary": "Brief AI-generated summary of the visit",
  "primary_diagnoses": [
    {
      "code": "I21.09",
      "code_system": "ICD10-CM",
      "description": "ST elevation myocardial infarction involving other coronary artery",
      "confidence_score": 0.92,
      "similarity_score": 0.97,
      "suggestion_type": "primary_diagnosis",
      "explanation": "Matched from: acute ST elevation myocardial infarction (STEMI)"
    }
  ],
  "secondary_diagnoses": [...],
  "procedures": [
    {
      "code": "92928",
      "code_system": "CPT",
      "description": "Percutaneous coronary intervention with stent placement",
      "confidence_score": 0.89,
      "similarity_score": 0.94,
      "suggestion_type": "procedure",
      "explanation": "Matched from: cardiac catheterization with drug-eluting stent placement"
    }
  ],
  "total_suggestions": 8,
  "processing_time_ms": 2450
}
```

## Example Usage

### Example 1: Acute MI with Intervention

```bash
curl -X POST "https://api.nuvii.ai/api/v1/clinical-coding" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient presents with acute chest pain radiating to left arm. History of hypertension and hyperlipidemia. EKG shows ST elevation in leads II, III, aVF. Diagnosed with acute ST elevation myocardial infarction (STEMI) involving the right coronary artery. Emergency cardiac catheterization performed with placement of drug-eluting stent to right coronary artery. Patient stabilized and transferred to ICU.",
    "max_codes_per_type": 5,
    "include_explanations": true
  }'
```

**Expected Results:**
- **Primary Diagnosis**: I21.09 (STEMI involving other coronary artery)
- **Secondary Diagnoses**: I10 (Hypertension), E78.5 (Hyperlipidemia)
- **Procedures**: 92928 (PCI with stent), 93458 (Cardiac catheterization)

### Example 2: Diabetes Management Visit

```bash
curl -X POST "https://api.nuvii.ai/api/v1/clinical-coding" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient with type 2 diabetes mellitus presents for follow-up. A1C today is 8.2%. Patient reports increased thirst and polyuria. Currently taking metformin 1000mg twice daily. Blood pressure 145/92. Foot exam shows no neuropathy. Retinal exam normal. Diagnosed with uncontrolled type 2 diabetes with hyperglycemia. Increased metformin to 1500mg twice daily. Ordered comprehensive metabolic panel and lipid panel.",
    "max_codes_per_type": 5,
    "include_explanations": true
  }'
```

**Expected Results:**
- **Primary Diagnosis**: E11.65 (Type 2 diabetes with hyperglycemia)
- **Secondary Diagnoses**: I10 (Hypertension)
- **Procedures**: 99214 (Office visit), 80053 (Comprehensive metabolic panel), 80061 (Lipid panel)

### Example 3: Surgical Procedure

```bash
curl -X POST "https://api.nuvii.ai/api/v1/clinical-coding" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient with right knee pain and locking for 3 months. MRI shows bucket handle tear of medial meniscus. Patient underwent arthroscopic partial medial meniscectomy under general anesthesia. Procedure performed successfully without complications. Post-op instructions given for physical therapy and gradual return to activities.",
    "max_codes_per_type": 5,
    "include_explanations": true
  }'
```

**Expected Results:**
- **Primary Diagnosis**: M23.204 (Derangement of medial meniscus, right knee)
- **Procedures**: 29881 (Arthroscopy knee with meniscectomy), 01400 (Anesthesia for knee arthroscopy)

## Python SDK Example

```python
import requests

API_KEY = "your_api_key_here"
API_URL = "https://api.nuvii.ai/api/v1/clinical-coding"

clinical_note = """
Patient presents with acute chest pain radiating to left arm.
History of hypertension. EKG shows ST elevation.
Diagnosed with acute STEMI. Emergency cardiac catheterization
performed with stent placement to right coronary artery.
"""

response = requests.post(
    API_URL,
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "clinical_note": clinical_note,
        "max_codes_per_type": 5,
        "include_explanations": True
    }
)

result = response.json()

print(f"Summary: {result['clinical_note_summary']}")
print(f"\nPrimary Diagnoses ({len(result['primary_diagnoses'])}):")
for code in result['primary_diagnoses']:
    print(f"  {code['code']}: {code['description']}")
    print(f"  Confidence: {code['confidence_score']:.2%}")
    print(f"  {code['explanation']}\n")

print(f"Procedures ({len(result['procedures'])}):")
for code in result['procedures']:
    print(f"  {code['code']}: {code['description']}")
    print(f"  Confidence: {code['confidence_score']:.2%}\n")
```

## Configuration

### Environment Variables

The endpoint requires the `ANTHROPIC_API_KEY` environment variable for LLM-powered entity extraction:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

If the API key is not set, the endpoint will fall back to basic keyword extraction (lower accuracy).

### Pricing Considerations

- **Semantic Search**: Uses existing MedCPT embeddings (no additional cost)
- **LLM Processing**: Uses Claude 3.5 Sonnet (~$3 per million tokens input, ~$15 per million tokens output)
- **Typical Note**: 500-1000 tokens input + 200 tokens output ≈ $0.005 per request

## Performance

- **Typical Processing Time**: 2-4 seconds
- **Accuracy**:
  - Entity extraction: 90-95% (with LLM)
  - Code matching: 85-90% (semantic search with 0.7+ similarity threshold)
- **Rate Limiting**: Subject to user's plan rate limits

## Best Practices

1. **Note Quality**: More detailed clinical notes yield better results
2. **Medical Terminology**: Use standard medical terminology for best matching
3. **Completeness**: Include diagnoses, procedures, and relevant history
4. **Verify Codes**: Always have coders review AI suggestions before billing
5. **Version Years**: Specify version_year to ensure code validity

## Limitations

- Requires ANTHROPIC_API_KEY for optimal accuracy
- Does not replace professional medical coding review
- May miss rare or complex diagnoses
- Code selection should be verified by certified coders
- Not intended for real-time billing without human oversight

## Error Handling

```json
{
  "detail": "Clinical coding failed: <error message>"
}
```

Common errors:
- `clinical_note too short`: Must be at least 50 characters
- `Rate limit exceeded`: User has exceeded their plan limits
- `Invalid API key`: Authentication failed

## Support

For questions or issues with the clinical coding endpoint:
- Email: support@nuvii.ai
- Documentation: https://api.nuvii.ai/docs
- Status: https://status.nuvii.ai
