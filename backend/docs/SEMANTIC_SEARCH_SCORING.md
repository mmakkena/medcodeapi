# Semantic Search Score Enhancement

## Problem

Semantic search using embedding vectors and cosine similarity often produces scores clustered in the 70-90% range, even for exact matches. This makes it difficult to:

1. **Distinguish quality** - Hard to tell excellent matches from good matches
2. **Set thresholds** - Difficult to filter low-quality results
3. **Rank results** - Poor differentiation between top results
4. **User confidence** - Users expect exact matches to score near 100%

## Root Causes

### 1. Embedding Model Limitations
- Even identical text can produce slightly different embeddings
- Floating-point precision and model variance
- Models optimize for semantic similarity, not exact matching

### 2. Score Distribution
- Cosine similarity naturally clusters in 0.7-0.9 range for related content
- Poor differentiation between exact and semantic matches
- Limited dynamic range in practice

### 3. Text Preprocessing
- Stored embeddings vs query embeddings may differ slightly
- Case sensitivity, whitespace, special characters
- Field selection (which description field was embedded)

## Solution Overview

The `search_enhancements.py` module provides three main improvements:

### 1. **Exact Match Detection & Boosting**
```python
def boost_score_with_exact_match(
    semantic_score: float,
    query: str,
    code: str,
    description: str,
    exact_match_boost: float = 0.2
) -> float
```

**What it does:**
- Detects when query exactly matches code or description
- Detects strong keyword matches (partial matches)
- Boosts scores proportionally to match quality

**Example:**
```
Query: "99213"
Raw score: 0.82
Enhanced score: 0.99 (exact code match detected)
```

### 2. **Score Calibration**
```python
def calibrate_semantic_score(
    raw_score: float,
    min_score: float = 0.5,
    max_score: float = 0.95,
    power: float = 0.6
) -> float
```

**What it does:**
- Remaps the typical 0.7-0.9 range to 0.0-1.0
- Applies power transformation to spread scores
- Better differentiates between match qualities

**Transformation:**
1. Normalize: `(score - min) / (max - min)`
2. Apply power: `normalized ^ power`
3. Result: Better spread across 0-1 range

**Example:**
```
Raw scores:     [0.85, 0.83, 0.81, 0.79, 0.75]
Calibrated:     [0.72, 0.66, 0.60, 0.54, 0.42]
(Better differentiation ↑)
```

### 3. **Keyword Matching**
```python
def detect_keyword_match(query: str, text: str) -> float
```

**What it does:**
- Calculates word-level overlap (Jaccard similarity)
- Detects substring matches
- Returns confidence score 0-1

**Example:**
```
Query: "office visit"
Text: "Office or other outpatient visit"
Keyword score: 0.67 (good overlap)
```

## Usage

### In Search Services

Both `procedure_search_service.py` and `icd10_search_service.py` now support:

```python
# With enhancement (default)
results = await semantic_search(
    db,
    "diabetic supplies",
    enhance_scores=True  # default
)

# Without enhancement (raw cosine similarity)
results = await semantic_search(
    db,
    "diabetic supplies",
    enhance_scores=False
)
```

### Direct Enhancement

```python
from app.services.search_enhancements import enhance_search_results

# Enhance existing results
enhanced = enhance_search_results(
    raw_results,
    query_text="knee surgery",
    code_field='code',
    description_fields=['short_desc', 'long_desc'],
    apply_calibration=True,
    apply_boosting=True,
    calibration_params={
        'min_score': 0.5,   # Adjust based on data
        'max_score': 0.95,
        'power': 0.6
    }
)
```

## Tuning Parameters

### Calibration Parameters

| Parameter | Default | Purpose | When to Adjust |
|-----------|---------|---------|----------------|
| `min_score` | 0.5 | Lower bound for normalization | If seeing many low-quality matches |
| `max_score` | 0.95 | Upper bound for normalization | Rarely needed (max realistic similarity) |
| `power` | 0.6 | Power transformation factor | Adjust score spread |

**Power parameter guide:**
- `< 1.0` - Spreads out high scores (recommended)
- `= 1.0` - Linear scaling (no transformation)
- `> 1.0` - Compresses high scores (not recommended)

### Exact Match Boost

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `exact_match_boost` | 0.2 | How much to boost exact matches |

**Tuning:**
- Increase if exact matches should dominate (e.g., 0.3)
- Decrease for more balanced semantic/exact weighting (e.g., 0.1)

## Testing

Run the test script to see before/after comparison:

```bash
cd backend
python scripts/test_semantic_scoring.py
```

Expected output:
```
Query: '99213'
─────────────────────────

📊 WITHOUT Enhancement:
  1. 99213    | Score: 0.8234 | Office outpatient visit

✨ WITH Enhancement:
  1. 99213    | Score: 0.9821 (+0.1587) | Office outpatient visit
```

## Monitoring

The enhancement module includes logging:

```python
from app.services.search_enhancements import log_score_distribution

log_score_distribution(results, "My Search")
# Logs: min=0.654, max=0.987, mean=0.823, count=10
```

Use this to:
1. Monitor score distributions in production
2. Identify when calibration params need adjustment
3. Debug score quality issues

## API Integration

No API changes required - enhancement is automatic. To expose control:

```python
# In API endpoint
@router.get("/procedure/search")
async def search_procedures(
    query: str,
    enhance_scores: bool = True,  # Allow API users to toggle
    db: Session = Depends(get_db)
):
    results = await semantic_search(
        db, query, enhance_scores=enhance_scores
    )
    ...
```

## Performance Impact

- **Minimal** - Enhancements run in Python (not DB)
- Extra computation: ~1-5ms per result set
- Trade-off: Slightly slower, much better quality

## When to Disable Enhancement

Keep `enhance_scores=False` when:

1. **Benchmark testing** - Compare raw model performance
2. **Research** - Analyzing pure embedding quality
3. **Performance critical** - Every millisecond matters
4. **Already calibrated** - If using different calibration system

## Examples

### Before Enhancement
```
Query: "office visit for diabetes"

Results:
1. 99213 | 0.814 | Office/outpatient visit
2. 99214 | 0.808 | Office/outpatient visit
3. 99204 | 0.803 | Office/outpatient new patient
```

Hard to differentiate, all scores similar.

### After Enhancement
```
Query: "office visit for diabetes"

Results:
1. 99213 | 0.943 | Office/outpatient visit (exact match boosted)
2. 99214 | 0.887 | Office/outpatient visit
3. 99204 | 0.791 | Office/outpatient new patient
```

Clear ranking, better differentiation.

## Troubleshooting

### Issue: Scores still clustered

**Solution:** Adjust calibration parameters
```python
calibration_params={
    'min_score': 0.6,   # Raise minimum
    'power': 0.5        # More aggressive spreading
}
```

### Issue: Exact matches not boosted enough

**Solution:** Increase exact match boost
```python
# In search_enhancements.py
boost_score_with_exact_match(
    semantic_score,
    query,
    code,
    description,
    exact_match_boost=0.3  # Increased from 0.2
)
```

### Issue: Irrelevant results scoring high

**Solution:** Increase min_similarity threshold
```python
results = await semantic_search(
    db,
    query,
    min_similarity=0.7,  # Only keep high-quality matches
    enhance_scores=True
)
```

## Future Improvements

Potential enhancements:

1. **Learned calibration** - Train calibration params on labeled data
2. **Query type detection** - Different params for codes vs text
3. **BM25 hybrid** - Combine with traditional search
4. **Re-ranking model** - Use cross-encoder for top results
5. **Field-specific boosting** - Weight code matches higher than description

## References

- Cosine similarity: https://en.wikipedia.org/wiki/Cosine_similarity
- Score calibration: https://en.wikipedia.org/wiki/Calibration_(statistics)
- Hybrid search: https://www.pinecone.io/learn/hybrid-search-intro/
