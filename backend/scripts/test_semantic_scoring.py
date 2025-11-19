#!/usr/bin/env python3
"""
Test script to compare raw vs enhanced semantic search scores.

This script helps verify that the score enhancement improvements are working
and shows the difference between raw cosine similarity and enhanced scores.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.procedure_search_service import semantic_search as proc_semantic_search
from app.services.icd10_search_service import semantic_search as icd_semantic_search


# Test queries designed to test exact matches, partial matches, and semantic matches
TEST_QUERIES = {
    "procedure": [
        # Exact code match
        ("99213", "Should match office visit code exactly"),
        # Exact description match
        ("office visit", "Should match E/M office visit codes"),
        # Semantic match
        ("diabetic supplies", "Semantic search for diabetes-related supplies"),
        # Medical terminology
        ("knee arthroscopy", "Surgical procedure search"),
        # Common procedure
        ("annual physical exam", "Preventive care visit"),
    ],
    "icd10": [
        # Exact code match
        ("I10", "Should match hypertension code exactly"),
        # Medical condition
        ("type 2 diabetes", "Common chronic condition"),
        # Symptom-based
        ("chest pain", "Common symptom"),
        # Specific diagnosis
        ("acute myocardial infarction", "Specific medical event"),
        # General category
        ("pneumonia", "Respiratory infection"),
    ]
}


async def test_procedure_search():
    """Test procedure code semantic search with and without enhancements."""
    print("\n" + "="*80)
    print("PROCEDURE CODE SEMANTIC SEARCH TEST")
    print("="*80)

    # Create database session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        for query, description in TEST_QUERIES["procedure"]:
            print(f"\n{'─'*80}")
            print(f"Query: '{query}'")
            print(f"Description: {description}")
            print(f"{'─'*80}")

            # Test without enhancement
            print("\n📊 WITHOUT Enhancement:")
            raw_results = await proc_semantic_search(
                db, query, limit=3, enhance_scores=False
            )

            for i, (code, score) in enumerate(raw_results, 1):
                print(f"  {i}. {code.code:8s} | Score: {score:.4f} | {code.short_desc or code.paraphrased_desc}")

            if not raw_results:
                print("  (No results)")

            # Test with enhancement
            print("\n✨ WITH Enhancement:")
            enhanced_results = await proc_semantic_search(
                db, query, limit=3, enhance_scores=True
            )

            for i, (code, score) in enumerate(enhanced_results, 1):
                raw_score = next((s for c, s in raw_results if c.code == code.code), 0.0)
                boost = score - raw_score
                boost_indicator = f"(+{boost:.4f})" if boost > 0.01 else ""

                print(f"  {i}. {code.code:8s} | Score: {score:.4f} {boost_indicator:12s} | {code.short_desc or code.paraphrased_desc}")

            if not enhanced_results:
                print("  (No results)")

    finally:
        db.close()


async def test_icd10_search():
    """Test ICD-10 code semantic search with and without enhancements."""
    print("\n" + "="*80)
    print("ICD-10 CODE SEMANTIC SEARCH TEST")
    print("="*80)

    # Create database session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        for query, description in TEST_QUERIES["icd10"]:
            print(f"\n{'─'*80}")
            print(f"Query: '{query}'")
            print(f"Description: {description}")
            print(f"{'─'*80}")

            # Test without enhancement
            print("\n📊 WITHOUT Enhancement:")
            raw_results = await icd_semantic_search(
                db, query, limit=3, enhance_scores=False
            )

            for i, (code, score) in enumerate(raw_results, 1):
                desc = code.short_desc or code.long_desc or code.description
                print(f"  {i}. {code.code:10s} | Score: {score:.4f} | {desc}")

            if not raw_results:
                print("  (No results)")

            # Test with enhancement
            print("\n✨ WITH Enhancement:")
            enhanced_results = await icd_semantic_search(
                db, query, limit=3, enhance_scores=True
            )

            for i, (code, score) in enumerate(enhanced_results, 1):
                raw_score = next((s for c, s in raw_results if c.code == code.code), 0.0)
                boost = score - raw_score
                boost_indicator = f"(+{boost:.4f})" if boost > 0.01 else ""

                desc = code.short_desc or code.long_desc or code.description
                print(f"  {i}. {code.code:10s} | Score: {score:.4f} {boost_indicator:12s} | {desc}")

            if not enhanced_results:
                print("  (No results)")

    finally:
        db.close()


async def main():
    """Run all tests."""
    print("\n" + "🔬 SEMANTIC SEARCH SCORE ENHANCEMENT TEST")
    print("This test compares raw cosine similarity scores with enhanced scores")
    print("that include exact match boosting and score calibration.\n")

    await test_procedure_search()
    await test_icd10_search()

    print("\n" + "="*80)
    print("✅ Test Complete")
    print("="*80)
    print("\nKey observations to look for:")
    print("1. Exact matches should score higher (closer to 1.0) with enhancement")
    print("2. Score distribution should be more spread out")
    print("3. Relevant results should rank higher")
    print()


if __name__ == "__main__":
    asyncio.run(main())
