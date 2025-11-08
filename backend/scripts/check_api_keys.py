#!/usr/bin/env python3
"""Check API keys in database"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection - use environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable is not set")
    exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_api_keys():
    """Check what API keys exist"""
    session = Session()

    try:
        # Check if api_keys table exists
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'api_keys'
            );
        """))

        table_exists = result.scalar()

        if not table_exists:
            print("❌ api_keys table does not exist")
            return

        # Get all API keys
        result = session.execute(text("""
            SELECT
                id,
                key,
                name,
                is_active,
                created_at,
                expires_at
            FROM api_keys
            ORDER BY created_at DESC
            LIMIT 10;
        """))

        rows = result.fetchall()

        if not rows:
            print("⚠️  No API keys found in database")
            return

        print(f"\n📋 Found {len(rows)} API keys:\n")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"Key: {row[1][:20]}... (truncated)")
            print(f"Name: {row[2]}")
            print(f"Active: {row[3]}")
            print(f"Created: {row[4]}")
            print(f"Expires: {row[5]}")
            print("-" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("API Keys Check")
    print("=" * 60)
    check_api_keys()
