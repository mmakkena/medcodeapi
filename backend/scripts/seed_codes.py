"""
Seed ICD-10 and CPT codes into the database.

This script:
1. Downloads CMS ICD-10 codes (public dataset)
2. Creates mock CPT codes (to be replaced with licensed data later)
3. Populates the database with search vectors for full-text search
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.icd10_code import ICD10Code
from app.models.cpt_code import CPTCode
from app.models.plan import Plan
from app.config import settings
import uuid

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def download_icd10_codes():
    """Download ICD-10 codes from CMS public dataset"""
    print("Downloading ICD-10 codes from CMS...")

    # CMS ICD-10 CM codes URL (2024 version)
    # Note: This is a simplified dataset. For production, use the full CMS dataset
    url = "https://www.cms.gov/medicare/coding-billing/icd-10-codes/2024-icd-10-cm"

    # For MVP, we'll create a sample dataset
    # In production, you would download and parse the actual CMS file
    sample_icd10_codes = [
        ("I10", "Essential (primary) hypertension", "Cardiovascular"),
        ("I11.0", "Hypertensive heart disease with heart failure", "Cardiovascular"),
        ("I11.9", "Hypertensive heart disease without heart failure", "Cardiovascular"),
        ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine"),
        ("E11.65", "Type 2 diabetes mellitus with hyperglycemia", "Endocrine"),
        ("E11.22", "Type 2 diabetes mellitus with diabetic chronic kidney disease", "Endocrine"),
        ("J44.0", "Chronic obstructive pulmonary disease with acute lower respiratory infection", "Respiratory"),
        ("J44.1", "Chronic obstructive pulmonary disease with acute exacerbation", "Respiratory"),
        ("J45.909", "Unspecified asthma, uncomplicated", "Respiratory"),
        ("Z79.4", "Long term (current) use of insulin", "Factors"),
        ("Z79.84", "Long term (current) use of oral hypoglycemic drugs", "Factors"),
        ("M79.3", "Panniculitis, unspecified", "Musculoskeletal"),
        ("M25.50", "Pain in unspecified joint", "Musculoskeletal"),
        ("F41.9", "Anxiety disorder, unspecified", "Mental"),
        ("F32.9", "Major depressive disorder, single episode, unspecified", "Mental"),
        ("R50.9", "Fever, unspecified", "Symptoms"),
        ("R51", "Headache", "Symptoms"),
        ("R53.83", "Other fatigue", "Symptoms"),
        ("Z00.00", "Encounter for general adult medical examination without abnormal findings", "Encounter"),
        ("Z23", "Encounter for immunization", "Encounter"),
    ]

    print(f"Loaded {len(sample_icd10_codes)} sample ICD-10 codes")
    print("Note: For production, download the full CMS ICD-10 dataset")

    return sample_icd10_codes


def create_mock_cpt_codes():
    """Create mock CPT codes (to be replaced with licensed data)"""
    print("Creating mock CPT codes...")

    mock_cpt_codes = [
        ("99213", "Office or other outpatient visit, established patient, 20-29 minutes", "Evaluation & Management"),
        ("99214", "Office or other outpatient visit, established patient, 30-39 minutes", "Evaluation & Management"),
        ("99215", "Office or other outpatient visit, established patient, 40-54 minutes", "Evaluation & Management"),
        ("99203", "Office or other outpatient visit, new patient, 30-44 minutes", "Evaluation & Management"),
        ("99204", "Office or other outpatient visit, new patient, 45-59 minutes", "Evaluation & Management"),
        ("99205", "Office or other outpatient visit, new patient, 60-74 minutes", "Evaluation & Management"),
        ("99385", "Initial comprehensive preventive medicine evaluation, 18-39 years", "Preventive Medicine"),
        ("99386", "Initial comprehensive preventive medicine evaluation, 40-64 years", "Preventive Medicine"),
        ("99395", "Periodic comprehensive preventive medicine reevaluation, 18-39 years", "Preventive Medicine"),
        ("99396", "Periodic comprehensive preventive medicine reevaluation, 40-64 years", "Preventive Medicine"),
        ("80053", "Comprehensive metabolic panel", "Laboratory"),
        ("85025", "Complete blood count (CBC) with differential", "Laboratory"),
        ("80061", "Lipid panel", "Laboratory"),
        ("83036", "Hemoglobin A1c level", "Laboratory"),
        ("93000", "Electrocardiogram, routine ECG with at least 12 leads", "Cardiovascular"),
        ("71046", "Radiologic examination, chest, 2 views", "Radiology"),
        ("71020", "Radiologic examination, chest, 1 view", "Radiology"),
        ("90471", "Immunization administration, first injection", "Immunization"),
        ("90472", "Immunization administration, each additional injection", "Immunization"),
        ("96127", "Brief emotional/behavioral assessment", "Behavioral Health"),
    ]

    print(f"Created {len(mock_cpt_codes)} mock CPT codes")
    print("Note: Replace with licensed CPT dataset for production")

    return mock_cpt_codes


def seed_plans():
    """Seed pricing plans"""
    print("Seeding pricing plans...")

    db = SessionLocal()

    plans_data = [
        {
            "name": "Free",
            "monthly_requests": 100,
            "price_cents": 0,
            "stripe_price_id": None,
            "features": {"rate_limit": "60/min", "support": "community"}
        },
        {
            "name": "Developer",
            "monthly_requests": 10000,
            "price_cents": 4900,
            "stripe_price_id": "price_developer",  # Replace with actual Stripe price ID
            "features": {"rate_limit": "300/min", "support": "email", "api_docs": True}
        },
        {
            "name": "Growth",
            "monthly_requests": 100000,
            "price_cents": 29900,
            "stripe_price_id": "price_growth",  # Replace with actual Stripe price ID
            "features": {"rate_limit": "1000/min", "support": "priority", "api_docs": True, "sla": "99.9%"}
        },
        {
            "name": "Enterprise",
            "monthly_requests": 1000000,
            "price_cents": 0,  # Custom pricing
            "stripe_price_id": None,
            "features": {"rate_limit": "custom", "support": "dedicated", "api_docs": True, "sla": "99.99%", "custom_integration": True}
        }
    ]

    for plan_data in plans_data:
        existing_plan = db.query(Plan).filter(Plan.name == plan_data["name"]).first()
        if not existing_plan:
            plan = Plan(**plan_data)
            db.add(plan)
            print(f"  Added plan: {plan_data['name']}")
        else:
            print(f"  Plan already exists: {plan_data['name']}")

    db.commit()
    db.close()
    print("Plans seeded successfully")


def seed_icd10_codes(codes_data):
    """Seed ICD-10 codes into database"""
    print("Seeding ICD-10 codes...")

    db = SessionLocal()

    # Clear existing codes
    db.query(ICD10Code).delete()
    db.commit()

    for code, description, category in codes_data:
        icd10 = ICD10Code(
            code=code,
            description=description,
            category=category
        )
        db.add(icd10)

    db.commit()

    # Create full-text search vectors
    print("Creating search vectors for ICD-10 codes...")
    db.execute(text("""
        UPDATE icd10_codes
        SET search_vector = to_tsvector('english', code || ' ' || description)
    """))
    db.commit()

    count = db.query(ICD10Code).count()
    db.close()

    print(f"Seeded {count} ICD-10 codes")


def seed_cpt_codes(codes_data):
    """Seed CPT codes into database"""
    print("Seeding CPT codes...")

    db = SessionLocal()

    # Clear existing codes
    db.query(CPTCode).delete()
    db.commit()

    for code, description, category in codes_data:
        cpt = CPTCode(
            code=code,
            description=description,
            category=category
        )
        db.add(cpt)

    db.commit()

    # Create full-text search vectors
    print("Creating search vectors for CPT codes...")
    db.execute(text("""
        UPDATE cpt_codes
        SET search_vector = to_tsvector('english', code || ' ' || description)
    """))
    db.commit()

    count = db.query(CPTCode).count()
    db.close()

    print(f"Seeded {count} CPT codes")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("MedCode API - Database Seeding")
    print("=" * 60)

    try:
        # Seed plans
        seed_plans()
        print()

        # Download and seed ICD-10 codes
        icd10_data = download_icd10_codes()
        seed_icd10_codes(icd10_data)
        print()

        # Create and seed mock CPT codes
        cpt_data = create_mock_cpt_codes()
        seed_cpt_codes(cpt_data)
        print()

        print("=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
