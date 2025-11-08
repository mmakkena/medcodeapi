#!/usr/bin/env python3
"""Test script to verify ICD-10 search functionality"""

import os
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

# Database connection - use environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable is not set")
    print("Please set it with: export DATABASE_URL='postgresql://...'")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def test_search(query: str, limit: int = 10):
    """Test search functionality similar to API endpoint"""
    session = Session()

    try:
        # Import the model
        from sqlalchemy import Column, String, Text
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        class ICD10Code(Base):
            __tablename__ = 'icd10_codes'

            id = Column(String, primary_key=True)
            code = Column(String)
            description = Column(Text)
            code_system = Column(String)
            year = Column(String)

        # Search by exact code match first
        results = session.query(ICD10Code).filter(
            ICD10Code.code.ilike(f"{query}%")
        ).limit(limit).all()

        # If no exact matches, do fuzzy text search on description
        if not results:
            results = session.query(ICD10Code).filter(
                ICD10Code.description.ilike(f"%{query}%")
            ).limit(limit).all()

        print(f"\n🔍 Search query: '{query}'")
        print(f"📊 Results found: {len(results)}\n")

        if results:
            for idx, result in enumerate(results, 1):
                print(f"{idx}. {result.code} - {result.description[:80]}")
                if len(result.description) > 80:
                    print(f"   {result.description[80:160]}...")
        else:
            print("❌ No results found")

        return len(results) > 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

def test_total_count():
    """Check total number of codes in database"""
    session = Session()

    try:
        from sqlalchemy import text
        result = session.execute(text("""
            SELECT
                code_system,
                COUNT(*) as total,
                COUNT(CASE WHEN code IS NOT NULL THEN 1 END) as with_code,
                COUNT(CASE WHEN description IS NOT NULL THEN 1 END) as with_description
            FROM icd10_codes
            WHERE code_system = 'ICD10-CM'
            GROUP BY code_system
        """))

        row = result.fetchone()
        if row:
            print(f"\n📈 Database Statistics:")
            print(f"   Code System: {row[0]}")
            print(f"   Total Codes: {row[1]:,}")
            print(f"   With Code: {row[2]:,}")
            print(f"   With Description: {row[3]:,}")

        return True
    except Exception as e:
        print(f"❌ Error checking count: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("ICD-10 Search Functionality Test")
    print("=" * 60)

    # Test 1: Check database statistics
    test_total_count()

    # Test 2: Search by code
    test_search("E11")

    # Test 3: Search by keyword
    test_search("diabetes")

    # Test 4: Search by another keyword
    test_search("hypertension")

    # Test 5: Search by specific code
    test_search("A00.0")

    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
