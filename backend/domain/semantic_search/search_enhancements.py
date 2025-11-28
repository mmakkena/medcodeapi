"""Search enhancement utilities for improved scoring and matching"""

import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
import math

logger = logging.getLogger(__name__)


def normalize_text_for_matching(text: str) -> str:
    """
    Normalize text for exact/partial match detection.

    Args:
        text: Input text

    Returns:
        Normalized text (lowercase, stripped, single spaces)
    """
    return ' '.join(text.lower().strip().split())


def detect_exact_match(query: str, code: str, description: str) -> bool:
    """
    Detect if query is an exact match for code or description.

    Args:
        query: Search query
        code: Medical code
        description: Code description

    Returns:
        True if exact match found
    """
    query_norm = normalize_text_for_matching(query)
    code_norm = normalize_text_for_matching(code)
    desc_norm = normalize_text_for_matching(description)

    return (
        query_norm == code_norm or
        query_norm == desc_norm or
        code_norm == query_norm or
        desc_norm == query_norm
    )


def detect_keyword_match(query: str, text: str) -> float:
    """
    Calculate keyword match score between query and text.

    Args:
        query: Search query
        text: Text to match against

    Returns:
        Match score between 0 and 1
    """
    query_norm = normalize_text_for_matching(query)
    text_norm = normalize_text_for_matching(text)

    # Exact match
    if query_norm == text_norm:
        return 1.0

    # Check if query is contained in text
    if query_norm in text_norm:
        # Score based on coverage (how much of the text matches)
        return len(query_norm) / len(text_norm)

    # Word-level matching
    query_words = set(query_norm.split())
    text_words = set(text_norm.split())

    if not query_words:
        return 0.0

    # Jaccard similarity
    intersection = query_words.intersection(text_words)
    union = query_words.union(text_words)

    return len(intersection) / len(union) if union else 0.0


def calibrate_semantic_score(
    raw_score: float,
    min_score: float = 0.0,
    max_score: float = 1.0,
    power: float = 0.5
) -> float:
    """
    Calibrate semantic similarity scores to better spread the distribution.

    Many embedding models cluster scores in the 0.7-0.9 range. This function
    applies transformations to better differentiate between matches.

    Args:
        raw_score: Raw similarity score from vector search (0-1)
        min_score: Minimum score to map to 0
        max_score: Maximum score to map to 1
        power: Power transformation (< 1 spreads out high scores, > 1 compresses)

    Returns:
        Calibrated score between 0 and 1
    """
    # Clip to valid range
    score = max(0.0, min(1.0, raw_score))

    # Normalize to [0, 1] range based on observed min/max
    if max_score > min_score:
        normalized = (score - min_score) / (max_score - min_score)
        normalized = max(0.0, min(1.0, normalized))
    else:
        normalized = score

    # Apply power transformation to spread scores
    calibrated = math.pow(normalized, power)

    return calibrated


def boost_score_with_exact_match(
    semantic_score: float,
    query: str,
    code: str,
    description: str,
    exact_match_boost: float = 0.2
) -> float:
    """
    Boost semantic score if exact or strong keyword match detected.

    Args:
        semantic_score: Base semantic similarity score
        query: Search query
        code: Medical code
        description: Code description
        exact_match_boost: How much to boost on exact match (0-1)

    Returns:
        Boosted score
    """
    # Check for exact match
    if detect_exact_match(query, code, description):
        # Boost to near-perfect score
        return min(1.0, semantic_score + exact_match_boost)

    # Check for strong keyword matches
    code_match = detect_keyword_match(query, code)
    desc_match = detect_keyword_match(query, description)

    # Use the best keyword match
    keyword_score = max(code_match, desc_match)

    # Boost semantic score proportionally to keyword match
    if keyword_score > 0.7:  # Strong keyword match
        boost = exact_match_boost * keyword_score
        return min(1.0, semantic_score + boost)

    return semantic_score


def enhance_search_results(
    results: List[Tuple[any, float]],
    query: str,
    code_field: str = 'code',
    description_fields: List[str] = ['short_desc', 'long_desc', 'description'],
    apply_calibration: bool = True,
    apply_boosting: bool = True,
    calibration_params: Optional[dict] = None
) -> List[Tuple[any, float]]:
    """
    Enhance search results with score calibration and exact match boosting.

    Args:
        results: List of (code_object, score) tuples from semantic search
        query: Original search query
        code_field: Name of field containing the code
        description_fields: List of fields to check for description text
        apply_calibration: Whether to apply score calibration
        apply_boosting: Whether to apply exact match boosting
        calibration_params: Optional calibration parameters

    Returns:
        Enhanced list of (code_object, enhanced_score) tuples
    """
    if not results:
        return results

    # Default calibration params (tune based on your data)
    default_calibration = {
        'min_score': 0.5,  # Scores below this get pushed toward 0
        'max_score': 0.95,  # Scores above this get pushed toward 1
        'power': 0.7  # Slightly spread out the scores
    }

    cal_params = calibration_params or default_calibration
    enhanced_results = []

    for code_obj, raw_score in results:
        score = raw_score

        # Apply calibration
        if apply_calibration:
            score = calibrate_semantic_score(
                score,
                min_score=cal_params.get('min_score', 0.5),
                max_score=cal_params.get('max_score', 0.95),
                power=cal_params.get('power', 0.7)
            )

        # Apply exact match boosting
        if apply_boosting:
            code_value = getattr(code_obj, code_field, '')

            # Get description from first available field
            description = ''
            for field in description_fields:
                desc = getattr(code_obj, field, None)
                if desc:
                    description = desc
                    break

            score = boost_score_with_exact_match(
                score,
                query,
                str(code_value),
                str(description)
            )

        enhanced_results.append((code_obj, score))

    # Re-sort by enhanced scores
    enhanced_results.sort(key=lambda x: x[1], reverse=True)

    return enhanced_results


def log_score_distribution(results: List[Tuple[any, float]], label: str = "Results"):
    """
    Log score distribution for debugging.

    Args:
        results: List of (code_object, score) tuples
        label: Label for the log message
    """
    if not results:
        logger.info(f"{label}: No results")
        return

    scores = [score for _, score in results]
    logger.info(
        f"{label} score distribution: "
        f"min={min(scores):.3f}, "
        f"max={max(scores):.3f}, "
        f"mean={sum(scores)/len(scores):.3f}, "
        f"count={len(scores)}"
    )
