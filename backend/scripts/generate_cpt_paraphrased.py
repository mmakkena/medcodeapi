#!/usr/bin/env python3
"""Generate paraphrased CPT code descriptions for 5000 most common codes

This script creates paraphrased descriptions for commonly used CPT codes
to avoid AMA copyright while providing useful procedure descriptions.

The descriptions are based on:
- Public CPT code number ranges (not copyrighted)
- Medical coding expertise and publicly available information
- Template-based generation avoiding AMA's exact wording

Usage:
    python scripts/generate_cpt_paraphrased.py --output data/procedure_codes/cpt_2025_expanded.csv
"""

import csv
import argparse
import logging
from pathlib import Path
from typing import List, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "procedure_codes"


def generate_em_codes() -> List[Dict]:
    """Generate E/M (Evaluation & Management) codes 99201-99499

    These are the most frequently used codes in medical practice.
    Expanded to ~250 codes covering all major E/M categories.
    """
    codes = []

    # Office visits - New patient (99202-99205)
    for i, level in enumerate([15, 30, 45, 60], start=2):
        codes.append({
            'code': f'9920{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Office visit for new patient, {level} minute typical time, medical decision making level {i-1}',
            'short_desc': '',
        })

    # Office visits - Established patient (99211-99215)
    codes.append({
        'code': '99211',
        'category': 'E/M',
        'paraphrased_desc': 'Brief office visit for established patient, minimal medical decision making',
        'short_desc': '',
    })
    for i, level in enumerate([10, 20, 30, 40], start=2):
        codes.append({
            'code': f'9921{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Office visit for established patient, {level} minute typical time, medical decision making level {i-1}',
            'short_desc': '',
        })

    # Observation care (99217-99220, 99224-99226, 99234-99236)
    codes.append({
        'code': '99217',
        'category': 'E/M',
        'paraphrased_desc': 'Observation care discharge day management',
        'short_desc': '',
    })
    for i, level in enumerate(['low', 'moderate', 'high'], start=8):
        codes.append({
            'code': f'9921{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Initial observation care, {level} complexity medical decision making',
            'short_desc': '',
        })
    for i, level in enumerate(['low', 'moderate', 'high'], start=4):
        codes.append({
            'code': f'9922{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Subsequent observation care, {level} complexity medical decision making',
            'short_desc': '',
        })
    for i, level in enumerate(['low', 'moderate', 'high'], start=4):
        codes.append({
            'code': f'9923{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Observation or inpatient same-day admission and discharge, {level} complexity',
            'short_desc': '',
        })

    # Initial hospital care (99221-99223)
    for i, level in enumerate(['low', 'moderate', 'high'], start=1):
        codes.append({
            'code': f'9922{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Initial hospital admission and evaluation, {level} complexity medical decision making',
            'short_desc': '',
        })

    # Subsequent hospital care (99231-99233)
    for i, level in enumerate(['low', 'moderate', 'high'], start=1):
        codes.append({
            'code': f'9923{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Follow-up hospital visit, {level} complexity medical decision making',
            'short_desc': '',
        })

    # Hospital discharge (99238-99239)
    codes.extend([
        {'code': '99238', 'category': 'E/M', 'paraphrased_desc': 'Hospital discharge management, 30 minutes or less', 'short_desc': ''},
        {'code': '99239', 'category': 'E/M', 'paraphrased_desc': 'Hospital discharge management, more than 30 minutes', 'short_desc': ''},
    ])

    # Emergency department (99281-99285)
    for i, level in enumerate(['minimal', 'low', 'moderate', 'high', 'critical'], start=1):
        codes.append({
            'code': f'9928{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Emergency department visit, {level} complexity medical decision making',
            'short_desc': '',
        })

    # Critical care (99291-99292)
    codes.extend([
        {'code': '99291', 'category': 'E/M', 'paraphrased_desc': 'Critical care services, first 30-74 minutes', 'short_desc': ''},
        {'code': '99292', 'category': 'E/M', 'paraphrased_desc': 'Critical care services, each additional 30 minutes', 'short_desc': ''},
    ])

    # Consultations - Office (99241-99245)
    for i, level in enumerate([20, 30, 40, 60, 80], start=1):
        codes.append({
            'code': f'9924{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Office consultation for new or established patient, {level} minute typical time',
            'short_desc': '',
        })

    # Consultations - Inpatient (99251-99255)
    for i, level in enumerate([20, 40, 55, 80, 110], start=1):
        codes.append({
            'code': f'9925{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Inpatient consultation, {level} minute typical time',
            'short_desc': '',
        })

    # Nursing facility services - Initial care (99304-99310)
    for i, level in enumerate(['low', 'moderate', 'high'], start=4):
        codes.append({
            'code': f'9930{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Initial nursing facility care, {level} complexity medical decision making',
            'short_desc': '',
        })
    for i, level in enumerate(['low', 'moderate', 'high'], start=7):
        codes.append({
            'code': f'9930{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Subsequent nursing facility care, {level} complexity medical decision making',
            'short_desc': '',
        })
    codes.append({
        'code': '99310',
        'category': 'E/M',
        'paraphrased_desc': 'Nursing facility discharge management, 30 minutes or less',
        'short_desc': '',
    })

    # Nursing facility services - Annual assessment (99318)
    codes.append({
        'code': '99318',
        'category': 'E/M',
        'paraphrased_desc': 'Annual nursing facility assessment',
        'short_desc': '',
    })

    # Domiciliary, rest home, or custodial care - New patient (99324-99328)
    for i, level in enumerate(['low', 'moderate', 'moderate-high', 'high', 'high complex'], start=4):
        codes.append({
            'code': f'9932{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Domiciliary or rest home visit, new patient, {level} complexity',
            'short_desc': '',
        })

    # Domiciliary, rest home, or custodial care - Established patient (99334-99337)
    for i, level in enumerate(['low', 'moderate', 'moderate-high', 'high'], start=4):
        codes.append({
            'code': f'9933{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Domiciliary or rest home visit, established patient, {level} complexity',
            'short_desc': '',
        })

    # Care plan oversight services (99339-99340)
    codes.extend([
        {'code': '99339', 'category': 'E/M', 'paraphrased_desc': 'Domiciliary care plan oversight, 15-29 minutes', 'short_desc': ''},
        {'code': '99340', 'category': 'E/M', 'paraphrased_desc': 'Domiciliary care plan oversight, 30 minutes or more', 'short_desc': ''},
    ])

    # Home services - New patient (99341-99345)
    for i, level in enumerate(['low', 'moderate', 'moderate-high', 'high', 'high complex'], start=1):
        codes.append({
            'code': f'9934{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Home visit, new patient, {level} complexity medical decision making',
            'short_desc': '',
        })

    # Home services - Established patient (99347-99350)
    for i, level in enumerate(['low', 'moderate', 'moderate-high', 'high'], start=7):
        codes.append({
            'code': f'9934{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Home visit, established patient, {level} complexity medical decision making',
            'short_desc': '',
        })

    # Preventive medicine - New patient (99381-99387)
    age_groups = ['infant', 'child 1-4', 'child 5-11', 'adolescent 12-17', 'adult 18-39', 'adult 40-64', 'adult 65+']
    for i, age in enumerate(age_groups, start=1):
        codes.append({
            'code': f'9938{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Preventive medicine visit for new patient, {age}',
            'short_desc': '',
        })

    # Preventive medicine - Established patient (99391-99397)
    for i, age in enumerate(age_groups, start=1):
        codes.append({
            'code': f'9939{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Preventive medicine visit for established patient, {age}',
            'short_desc': '',
        })

    # Prolonged services (99354-99357)
    codes.extend([
        {'code': '99354', 'category': 'E/M', 'paraphrased_desc': 'Prolonged outpatient service, first hour', 'short_desc': ''},
        {'code': '99355', 'category': 'E/M', 'paraphrased_desc': 'Prolonged outpatient service, additional 30 minutes', 'short_desc': ''},
        {'code': '99356', 'category': 'E/M', 'paraphrased_desc': 'Prolonged inpatient service, first hour', 'short_desc': ''},
        {'code': '99357', 'category': 'E/M', 'paraphrased_desc': 'Prolonged inpatient service, additional 30 minutes', 'short_desc': ''},
    ])

    # Medical team conferences (99366-99368)
    codes.extend([
        {'code': '99366', 'category': 'E/M', 'paraphrased_desc': 'Medical team conference with interdisciplinary team, 30 minutes', 'short_desc': ''},
        {'code': '99367', 'category': 'E/M', 'paraphrased_desc': 'Medical team conference with patient or family present, 30 minutes', 'short_desc': ''},
        {'code': '99368', 'category': 'E/M', 'paraphrased_desc': 'Medical team conference without patient present, 30 minutes', 'short_desc': ''},
    ])

    # Care plan oversight (99374-99380)
    codes.extend([
        {'code': '99374', 'category': 'E/M', 'paraphrased_desc': 'Care plan oversight for home health, 15-29 minutes', 'short_desc': ''},
        {'code': '99375', 'category': 'E/M', 'paraphrased_desc': 'Care plan oversight for home health, 30 minutes or more', 'short_desc': ''},
        {'code': '99377', 'category': 'E/M', 'paraphrased_desc': 'Care plan oversight for hospice, 15-29 minutes', 'short_desc': ''},
        {'code': '99378', 'category': 'E/M', 'paraphrased_desc': 'Care plan oversight for hospice, 30 minutes or more', 'short_desc': ''},
        {'code': '99379', 'category': 'E/M', 'paraphrased_desc': 'Care plan oversight for nursing facility, 15-29 minutes', 'short_desc': ''},
        {'code': '99380', 'category': 'E/M', 'paraphrased_desc': 'Care plan oversight for nursing facility, 30 minutes or more', 'short_desc': ''},
    ])

    # Newborn care services (99460-99465)
    codes.extend([
        {'code': '99460', 'category': 'E/M', 'paraphrased_desc': 'Initial hospital or birthing center care, newborn evaluation', 'short_desc': ''},
        {'code': '99461', 'category': 'E/M', 'paraphrased_desc': 'Initial care, normal newborn in other than hospital or birthing center', 'short_desc': ''},
        {'code': '99462', 'category': 'E/M', 'paraphrased_desc': 'Subsequent hospital care, normal newborn', 'short_desc': ''},
        {'code': '99463', 'category': 'E/M', 'paraphrased_desc': 'Initial hospital or birthing center care, normal newborn', 'short_desc': ''},
        {'code': '99464', 'category': 'E/M', 'paraphrased_desc': 'Attendance at delivery and initial stabilization of newborn', 'short_desc': ''},
        {'code': '99465', 'category': 'E/M', 'paraphrased_desc': 'Delivery room or resuscitation, standby services', 'short_desc': ''},
    ])

    # Neonatal and pediatric critical care (99468-99476)
    codes.extend([
        {'code': '99468', 'category': 'E/M', 'paraphrased_desc': 'Initial inpatient neonatal critical care, neonate 28 days or younger', 'short_desc': ''},
        {'code': '99469', 'category': 'E/M', 'paraphrased_desc': 'Subsequent inpatient neonatal critical care, neonate 28 days or younger', 'short_desc': ''},
        {'code': '99471', 'category': 'E/M', 'paraphrased_desc': 'Initial inpatient pediatric critical care, infant 29 days through 24 months', 'short_desc': ''},
        {'code': '99472', 'category': 'E/M', 'paraphrased_desc': 'Subsequent inpatient pediatric critical care, infant 29 days through 24 months', 'short_desc': ''},
        {'code': '99475', 'category': 'E/M', 'paraphrased_desc': 'Initial inpatient pediatric critical care, child 2-5 years', 'short_desc': ''},
        {'code': '99476', 'category': 'E/M', 'paraphrased_desc': 'Subsequent inpatient pediatric critical care, child 2-5 years', 'short_desc': ''},
    ])

    # Chronic care management (99490-99491)
    codes.extend([
        {'code': '99490', 'category': 'E/M', 'paraphrased_desc': 'Chronic care management services, 20 minutes minimum', 'short_desc': ''},
        {'code': '99491', 'category': 'E/M', 'paraphrased_desc': 'Chronic care management services, 30 minutes minimum', 'short_desc': ''},
    ])

    # Transitional care management (99495-99496)
    codes.extend([
        {'code': '99495', 'category': 'E/M', 'paraphrased_desc': 'Transitional care management, moderate complexity', 'short_desc': ''},
        {'code': '99496', 'category': 'E/M', 'paraphrased_desc': 'Transitional care management, high complexity', 'short_desc': ''},
    ])

    # Advance care planning (99497-99498)
    codes.extend([
        {'code': '99497', 'category': 'E/M', 'paraphrased_desc': 'Advance care planning, first 30 minutes', 'short_desc': ''},
        {'code': '99498', 'category': 'E/M', 'paraphrased_desc': 'Advance care planning, additional 30 minutes', 'short_desc': ''},
    ])

    # Telehealth (99421-99423, 99441-99443, 99446-99449, 99451-99452)
    for i, mins in enumerate([5, 10, 20], start=1):
        codes.append({
            'code': f'9942{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Online digital evaluation and management service, {mins} minutes',
            'short_desc': '',
        })
        codes.append({
            'code': f'9944{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Telephone evaluation and management service, {mins} minutes',
            'short_desc': '',
        })

    # Interprofessional telephone/internet consultation (99446-99449)
    for i, mins in enumerate([5, 10, 20, 30], start=6):
        codes.append({
            'code': f'9944{i}',
            'category': 'E/M',
            'paraphrased_desc': f'Interprofessional telephone or internet assessment, {mins} minutes',
            'short_desc': '',
        })

    # Digitally stored data services (99453-99454, 99457-99458)
    codes.extend([
        {'code': '99453', 'category': 'E/M', 'paraphrased_desc': 'Remote monitoring of physiologic parameters, initial setup', 'short_desc': ''},
        {'code': '99454', 'category': 'E/M', 'paraphrased_desc': 'Remote monitoring device supply, each 30 days', 'short_desc': ''},
        {'code': '99457', 'category': 'E/M', 'paraphrased_desc': 'Remote physiologic monitoring treatment, first 20 minutes', 'short_desc': ''},
        {'code': '99458', 'category': 'E/M', 'paraphrased_desc': 'Remote physiologic monitoring treatment, additional 20 minutes', 'short_desc': ''},
    ])

    logger.info(f"Generated {len(codes)} E/M codes")
    return codes


def generate_lab_codes() -> List[Dict]:
    """Generate common Laboratory codes 80000-89999

    Expanded to ~350 codes covering comprehensive laboratory testing.
    """
    codes = []

    # Basic metabolic panel and variations (80047-80053)
    codes.extend([
        {'code': '80047', 'category': 'Laboratory', 'paraphrased_desc': 'Basic metabolic panel with calcium, 8 tests', 'short_desc': ''},
        {'code': '80048', 'category': 'Laboratory', 'paraphrased_desc': 'Basic metabolic panel, 8 tests', 'short_desc': ''},
        {'code': '80050', 'category': 'Laboratory', 'paraphrased_desc': 'General health panel', 'short_desc': ''},
        {'code': '80053', 'category': 'Laboratory', 'paraphrased_desc': 'Comprehensive metabolic panel, 14 tests', 'short_desc': ''},
    ])

    # Lipid panel (80061)
    codes.append({
        'code': '80061',
        'category': 'Laboratory',
        'paraphrased_desc': 'Lipid panel with total cholesterol, HDL, LDL, triglycerides',
        'short_desc': '',
    })

    # Hepatic function panel (80076)
    codes.append({
        'code': '80076',
        'category': 'Laboratory',
        'paraphrased_desc': 'Liver function panel with albumin, bilirubin, ALT, AST, alkaline phosphatase',
        'short_desc': '',
    })

    # Renal function panel (80069)
    codes.append({
        'code': '80069',
        'category': 'Laboratory',
        'paraphrased_desc': 'Kidney function panel with albumin, calcium, carbon dioxide, chloride, creatinine, glucose, phosphorus, potassium, sodium, urea',
        'short_desc': '',
    })

    # Complete blood count (85025-85027)
    codes.extend([
        {'code': '85025', 'category': 'Laboratory', 'paraphrased_desc': 'Complete blood count with automated differential', 'short_desc': ''},
        {'code': '85027', 'category': 'Laboratory', 'paraphrased_desc': 'Complete blood count with manual differential', 'short_desc': ''},
        {'code': '85004', 'category': 'Laboratory', 'paraphrased_desc': 'Blood count, automated differential WBC', 'short_desc': ''},
    ])

    # Hemoglobin A1c (83036-83037)
    codes.extend([
        {'code': '83036', 'category': 'Laboratory', 'paraphrased_desc': 'Hemoglobin A1c test for diabetes monitoring', 'short_desc': ''},
        {'code': '83037', 'category': 'Laboratory', 'paraphrased_desc': 'Hemoglobin glycosylated', 'short_desc': ''},
    ])

    # Thyroid tests (84436-84443, 84479-84482)
    codes.extend([
        {'code': '84436', 'category': 'Laboratory', 'paraphrased_desc': 'Thyroxine (T4) total', 'short_desc': ''},
        {'code': '84439', 'category': 'Laboratory', 'paraphrased_desc': 'Thyroxine (T4) free', 'short_desc': ''},
        {'code': '84443', 'category': 'Laboratory', 'paraphrased_desc': 'Thyroid stimulating hormone (TSH)', 'short_desc': ''},
        {'code': '84480', 'category': 'Laboratory', 'paraphrased_desc': 'Triiodothyronine (T3) total', 'short_desc': ''},
        {'code': '84481', 'category': 'Laboratory', 'paraphrased_desc': 'Triiodothyronine (T3) free', 'short_desc': ''},
    ])

    # Glucose tests (82947-82950)
    codes.extend([
        {'code': '82947', 'category': 'Laboratory', 'paraphrased_desc': 'Glucose blood test, quantitative', 'short_desc': ''},
        {'code': '82950', 'category': 'Laboratory', 'paraphrased_desc': 'Glucose tolerance test, 3 specimens', 'short_desc': ''},
        {'code': '82951', 'category': 'Laboratory', 'paraphrased_desc': 'Glucose tolerance test, additional specimens', 'short_desc': ''},
    ])

    # Urinalysis (81000-81003, 81007)
    codes.extend([
        {'code': '81000', 'category': 'Laboratory', 'paraphrased_desc': 'Urinalysis, manual test without microscopy', 'short_desc': ''},
        {'code': '81001', 'category': 'Laboratory', 'paraphrased_desc': 'Urinalysis, automated without microscopy', 'short_desc': ''},
        {'code': '81002', 'category': 'Laboratory', 'paraphrased_desc': 'Urinalysis, manual test with microscopy', 'short_desc': ''},
        {'code': '81003', 'category': 'Laboratory', 'paraphrased_desc': 'Urinalysis, automated with microscopy', 'short_desc': ''},
        {'code': '81007', 'category': 'Laboratory', 'paraphrased_desc': 'Urinalysis, bacteriuria screen', 'short_desc': ''},
    ])

    # Prostate specific antigen (84153-84154)
    codes.extend([
        {'code': '84153', 'category': 'Laboratory', 'paraphrased_desc': 'Prostate specific antigen (PSA) total', 'short_desc': ''},
        {'code': '84154', 'category': 'Laboratory', 'paraphrased_desc': 'Prostate specific antigen (PSA) free', 'short_desc': ''},
    ])

    # Vitamin D (82306)
    codes.append({
        'code': '82306',
        'category': 'Laboratory',
        'paraphrased_desc': 'Vitamin D, 25-hydroxy measurement',
        'short_desc': '',
    })

    # Vitamin B12 and folate (82607-82608)
    codes.extend([
        {'code': '82607', 'category': 'Laboratory', 'paraphrased_desc': 'Vitamin B12 measurement', 'short_desc': ''},
        {'code': '82746', 'category': 'Laboratory', 'paraphrased_desc': 'Folic acid (folate) serum', 'short_desc': ''},
    ])

    # Iron studies (83540, 83550, 84466)
    codes.extend([
        {'code': '83540', 'category': 'Laboratory', 'paraphrased_desc': 'Iron serum measurement', 'short_desc': ''},
        {'code': '83550', 'category': 'Laboratory', 'paraphrased_desc': 'Iron binding capacity measurement', 'short_desc': ''},
        {'code': '84466', 'category': 'Laboratory', 'paraphrased_desc': 'Transferrin measurement', 'short_desc': ''},
    ])

    # Ferritin (82728)
    codes.append({
        'code': '82728',
        'category': 'Laboratory',
        'paraphrased_desc': 'Ferritin measurement',
        'short_desc': '',
    })

    # Troponin (84484)
    codes.append({
        'code': '84484',
        'category': 'Laboratory',
        'paraphrased_desc': 'Troponin, quantitative cardiac marker',
        'short_desc': '',
    })

    # BNP (83880)
    codes.append({
        'code': '83880',
        'category': 'Laboratory',
        'paraphrased_desc': 'B-type natriuretic peptide (BNP) for heart failure assessment',
        'short_desc': '',
    })

    # Creatinine (82565)
    codes.append({
        'code': '82565',
        'category': 'Laboratory',
        'paraphrased_desc': 'Creatinine blood test',
        'short_desc': '',
    })

    # Electrolytes
    codes.extend([
        {'code': '82435', 'category': 'Laboratory', 'paraphrased_desc': 'Chloride blood test', 'short_desc': ''},
        {'code': '82374', 'category': 'Laboratory', 'paraphrased_desc': 'Carbon dioxide (bicarbonate)', 'short_desc': ''},
        {'code': '84132', 'category': 'Laboratory', 'paraphrased_desc': 'Potassium serum', 'short_desc': ''},
        {'code': '84295', 'category': 'Laboratory', 'paraphrased_desc': 'Sodium serum', 'short_desc': ''},
    ])

    # Liver enzymes
    codes.extend([
        {'code': '84460', 'category': 'Laboratory', 'paraphrased_desc': 'Alanine aminotransferase (ALT/SGPT)', 'short_desc': ''},
        {'code': '84450', 'category': 'Laboratory', 'paraphrased_desc': 'Aspartate aminotransferase (AST/SGOT)', 'short_desc': ''},
        {'code': '84075', 'category': 'Laboratory', 'paraphrased_desc': 'Alkaline phosphatase', 'short_desc': ''},
        {'code': '82040', 'category': 'Laboratory', 'paraphrased_desc': 'Albumin serum', 'short_desc': ''},
    ])

    # Bilirubin (82247-82248)
    codes.extend([
        {'code': '82247', 'category': 'Laboratory', 'paraphrased_desc': 'Bilirubin total', 'short_desc': ''},
        {'code': '82248', 'category': 'Laboratory', 'paraphrased_desc': 'Bilirubin direct', 'short_desc': ''},
    ])

    # Uric acid (84550)
    codes.append({
        'code': '84550',
        'category': 'Laboratory',
        'paraphrased_desc': 'Uric acid blood test',
        'short_desc': '',
    })

    # Calcium (82310)
    codes.append({
        'code': '82310',
        'category': 'Laboratory',
        'paraphrased_desc': 'Calcium total',
        'short_desc': '',
    })

    # Magnesium (83735)
    codes.append({
        'code': '83735',
        'category': 'Laboratory',
        'paraphrased_desc': 'Magnesium measurement',
        'short_desc': '',
    })

    # Phosphorus (84100)
    codes.append({
        'code': '84100',
        'category': 'Laboratory',
        'paraphrased_desc': 'Phosphorus inorganic (phosphate)',
        'short_desc': '',
    })

    # Prothrombin time (85610)
    codes.append({
        'code': '85610',
        'category': 'Laboratory',
        'paraphrased_desc': 'Prothrombin time (PT)',
        'short_desc': '',
    })

    # Partial thromboplastin time (85730)
    codes.append({
        'code': '85730',
        'category': 'Laboratory',
        'paraphrased_desc': 'Partial thromboplastin time (PTT)',
        'short_desc': '',
    })

    # INR (85610 above)

    # Cultures (87040-87088)
    codes.extend([
        {'code': '87040', 'category': 'Laboratory', 'paraphrased_desc': 'Blood culture for bacteria', 'short_desc': ''},
        {'code': '87045', 'category': 'Laboratory', 'paraphrased_desc': 'Stool culture for bacteria', 'short_desc': ''},
        {'code': '87070', 'category': 'Laboratory', 'paraphrased_desc': 'Culture bacterial, any source except urine, blood, or stool', 'short_desc': ''},
        {'code': '87086', 'category': 'Laboratory', 'paraphrased_desc': 'Urine culture for bacteria', 'short_desc': ''},
        {'code': '87088', 'category': 'Laboratory', 'paraphrased_desc': 'Urine culture for bacteria with colony count', 'short_desc': ''},
    ])

    # Strep test (87880)
    codes.append({
        'code': '87880',
        'category': 'Laboratory',
        'paraphrased_desc': 'Streptococcus group A rapid test',
        'short_desc': '',
    })

    # Influenza test (87804)
    codes.append({
        'code': '87804',
        'category': 'Laboratory',
        'paraphrased_desc': 'Influenza virus detection',
        'short_desc': '',
    })

    # COVID-19 tests (87635)
    codes.append({
        'code': '87635',
        'category': 'Laboratory',
        'paraphrased_desc': 'SARS-CoV-2 (COVID-19) detection',
        'short_desc': '',
    })

    # Pregnancy test (84703)
    codes.append({
        'code': '84703',
        'category': 'Laboratory',
        'paraphrased_desc': 'Human chorionic gonadotropin (HCG) qualitative pregnancy test',
        'short_desc': '',
    })

    # Drug screening (80305-80307)
    codes.extend([
        {'code': '80305', 'category': 'Laboratory', 'paraphrased_desc': 'Drug test, presumptive, any number of drug classes', 'short_desc': ''},
        {'code': '80306', 'category': 'Laboratory', 'paraphrased_desc': 'Drug test, presumptive, read by instrument', 'short_desc': ''},
        {'code': '80307', 'category': 'Laboratory', 'paraphrased_desc': 'Drug test, presumptive, by chemistry analyzers', 'short_desc': ''},
    ])

    # EXPANSION: Additional Hormones
    codes.extend([
        {'code': '82670', 'category': 'Laboratory', 'paraphrased_desc': 'Estradiol measurement', 'short_desc': ''},
        {'code': '84402', 'category': 'Laboratory', 'paraphrased_desc': 'Testosterone, total', 'short_desc': ''},
        {'code': '84403', 'category': 'Laboratory', 'paraphrased_desc': 'Testosterone, free', 'short_desc': ''},
        {'code': '84144', 'category': 'Laboratory', 'paraphrased_desc': 'Progesterone measurement', 'short_desc': ''},
        {'code': '82533', 'category': 'Laboratory', 'paraphrased_desc': 'Cortisol, total', 'short_desc': ''},
        {'code': '82530', 'category': 'Laboratory', 'paraphrased_desc': 'Cortisol, free', 'short_desc': ''},
        {'code': '82024', 'category': 'Laboratory', 'paraphrased_desc': 'ACTH (adrenocorticotropic hormone)', 'short_desc': ''},
        {'code': '83001', 'category': 'Laboratory', 'paraphrased_desc': 'FSH (follicle stimulating hormone)', 'short_desc': ''},
        {'code': '83002', 'category': 'Laboratory', 'paraphrased_desc': 'LH (luteinizing hormone)', 'short_desc': ''},
        {'code': '83003', 'category': 'Laboratory', 'paraphrased_desc': 'Growth hormone', 'short_desc': ''},
        {'code': '84146', 'category': 'Laboratory', 'paraphrased_desc': 'Prolactin measurement', 'short_desc': ''},
        {'code': '84305', 'category': 'Laboratory', 'paraphrased_desc': 'Somatomedin (IGF-1)', 'short_desc': ''},
        {'code': '82626', 'category': 'Laboratory', 'paraphrased_desc': 'DHEA (dehydroepiandrosterone)', 'short_desc': ''},
        {'code': '82627', 'category': 'Laboratory', 'paraphrased_desc': 'DHEA-sulfate', 'short_desc': ''},
        {'code': '83498', 'category': 'Laboratory', 'paraphrased_desc': 'Hydroxyprogesterone, 17-D', 'short_desc': ''},
        {'code': '84449', 'category': 'Laboratory', 'paraphrased_desc': 'SHBG (sex hormone binding globulin)', 'short_desc': ''},
        {'code': '84145', 'category': 'Laboratory', 'paraphrased_desc': 'Procalcitonin', 'short_desc': ''},
        {'code': '83519', 'category': 'Laboratory', 'paraphrased_desc': 'Immunoassay, qualitative or semiquantitative', 'short_desc': ''},
    ])

    # EXPANSION: Tumor Markers
    codes.extend([
        {'code': '82378', 'category': 'Laboratory', 'paraphrased_desc': 'CEA (carcinoembryonic antigen)', 'short_desc': ''},
        {'code': '86304', 'category': 'Laboratory', 'paraphrased_desc': 'CA 19-9 (cancer antigen 19-9)', 'short_desc': ''},
        {'code': '86300', 'category': 'Laboratory', 'paraphrased_desc': 'CA 125 (cancer antigen 125)', 'short_desc': ''},
        {'code': '86316', 'category': 'Laboratory', 'paraphrased_desc': 'CA 15-3 (cancer antigen 15-3)', 'short_desc': ''},
        {'code': '86301', 'category': 'Laboratory', 'paraphrased_desc': 'CA 27-29 (cancer antigen 27-29)', 'short_desc': ''},
        {'code': '82105', 'category': 'Laboratory', 'paraphrased_desc': 'AFP (alpha-fetoprotein), serum', 'short_desc': ''},
        {'code': '82106', 'category': 'Laboratory', 'paraphrased_desc': 'AFP (alpha-fetoprotein), amniotic fluid', 'short_desc': ''},
        {'code': '84152', 'category': 'Laboratory', 'paraphrased_desc': 'PSA (prostate specific antigen), complexed', 'short_desc': ''},
        {'code': '83520', 'category': 'Laboratory', 'paraphrased_desc': 'Immunoassay, tumor antigen, quantitative', 'short_desc': ''},
        {'code': '84999', 'category': 'Laboratory', 'paraphrased_desc': 'Unlisted chemistry procedure', 'short_desc': ''},
    ])

    # EXPANSION: Therapeutic Drug Levels
    codes.extend([
        {'code': '80162', 'category': 'Laboratory', 'paraphrased_desc': 'Digoxin therapeutic drug level', 'short_desc': ''},
        {'code': '80178', 'category': 'Laboratory', 'paraphrased_desc': 'Lithium therapeutic drug level', 'short_desc': ''},
        {'code': '80185', 'category': 'Laboratory', 'paraphrased_desc': 'Phenytoin (Dilantin) level, total', 'short_desc': ''},
        {'code': '80186', 'category': 'Laboratory', 'paraphrased_desc': 'Phenytoin (Dilantin) level, free', 'short_desc': ''},
        {'code': '80164', 'category': 'Laboratory', 'paraphrased_desc': 'Valproic acid (Depakote) level, total', 'short_desc': ''},
        {'code': '80165', 'category': 'Laboratory', 'paraphrased_desc': 'Valproic acid (Depakote) level, free', 'short_desc': ''},
        {'code': '80150', 'category': 'Laboratory', 'paraphrased_desc': 'Amikacin therapeutic drug level', 'short_desc': ''},
        {'code': '80155', 'category': 'Laboratory', 'paraphrased_desc': 'Caffeine therapeutic drug level', 'short_desc': ''},
        {'code': '80156', 'category': 'Laboratory', 'paraphrased_desc': 'Carbamazepine (Tegretol) level, total', 'short_desc': ''},
        {'code': '80157', 'category': 'Laboratory', 'paraphrased_desc': 'Carbamazepine (Tegretol) level, free', 'short_desc': ''},
        {'code': '80159', 'category': 'Laboratory', 'paraphrased_desc': 'Clozapine therapeutic drug level', 'short_desc': ''},
        {'code': '80160', 'category': 'Laboratory', 'paraphrased_desc': 'Desipramine therapeutic drug level', 'short_desc': ''},
        {'code': '80168', 'category': 'Laboratory', 'paraphrased_desc': 'Gentamicin therapeutic drug level', 'short_desc': ''},
        {'code': '80171', 'category': 'Laboratory', 'paraphrased_desc': 'Gabapentin (Neurontin) level', 'short_desc': ''},
        {'code': '80173', 'category': 'Laboratory', 'paraphrased_desc': 'Haloperidol therapeutic drug level', 'short_desc': ''},
        {'code': '80177', 'category': 'Laboratory', 'paraphrased_desc': 'Levetiracetam (Keppra) level', 'short_desc': ''},
        {'code': '80183', 'category': 'Laboratory', 'paraphrased_desc': 'Oxcarbazepine (Trileptal) level', 'short_desc': ''},
        {'code': '80184', 'category': 'Laboratory', 'paraphrased_desc': 'Phenobarbital level', 'short_desc': ''},
        {'code': '80188', 'category': 'Laboratory', 'paraphrased_desc': 'Primidone level', 'short_desc': ''},
        {'code': '80190', 'category': 'Laboratory', 'paraphrased_desc': 'Procainamide therapeutic drug level', 'short_desc': ''},
        {'code': '80192', 'category': 'Laboratory', 'paraphrased_desc': 'Quinidine therapeutic drug level', 'short_desc': ''},
        {'code': '80194', 'category': 'Laboratory', 'paraphrased_desc': 'Quinidine therapeutic drug level', 'short_desc': ''},
        {'code': '80195', 'category': 'Laboratory', 'paraphrased_desc': 'Sirolimus therapeutic drug level', 'short_desc': ''},
        {'code': '80197', 'category': 'Laboratory', 'paraphrased_desc': 'Tacrolimus therapeutic drug level', 'short_desc': ''},
        {'code': '80198', 'category': 'Laboratory', 'paraphrased_desc': 'Theophylline therapeutic drug level', 'short_desc': ''},
        {'code': '80199', 'category': 'Laboratory', 'paraphrased_desc': 'Tiagabine therapeutic drug level', 'short_desc': ''},
        {'code': '80200', 'category': 'Laboratory', 'paraphrased_desc': 'Tobramycin therapeutic drug level', 'short_desc': ''},
        {'code': '80201', 'category': 'Laboratory', 'paraphrased_desc': 'Topiramate therapeutic drug level', 'short_desc': ''},
        {'code': '80202', 'category': 'Laboratory', 'paraphrased_desc': 'Vancomycin therapeutic drug level', 'short_desc': ''},
        {'code': '80203', 'category': 'Laboratory', 'paraphrased_desc': 'Zonisamide therapeutic drug level', 'short_desc': ''},
    ])

    # EXPANSION: Coagulation Tests
    codes.extend([
        {'code': '85379', 'category': 'Laboratory', 'paraphrased_desc': 'Fibrin degradation products (D-dimer), qualitative', 'short_desc': ''},
        {'code': '85378', 'category': 'Laboratory', 'paraphrased_desc': 'Fibrin degradation products (D-dimer), quantitative', 'short_desc': ''},
        {'code': '85384', 'category': 'Laboratory', 'paraphrased_desc': 'Fibrinogen activity', 'short_desc': ''},
        {'code': '85385', 'category': 'Laboratory', 'paraphrased_desc': 'Fibrinogen antigen', 'short_desc': ''},
        {'code': '85337', 'category': 'Laboratory', 'paraphrased_desc': 'Thrombin time', 'short_desc': ''},
        {'code': '85345', 'category': 'Laboratory', 'paraphrased_desc': 'Coagulation time, Lee and White', 'short_desc': ''},
        {'code': '85348', 'category': 'Laboratory', 'paraphrased_desc': 'Coagulation time, other methods', 'short_desc': ''},
        {'code': '85362', 'category': 'Laboratory', 'paraphrased_desc': 'Fibrin degradation products, qualitative', 'short_desc': ''},
        {'code': '85366', 'category': 'Laboratory', 'paraphrased_desc': 'Fibrin degradation products, quantitative', 'short_desc': ''},
        {'code': '85370', 'category': 'Laboratory', 'paraphrased_desc': 'Clot retraction test', 'short_desc': ''},
        {'code': '85396', 'category': 'Laboratory', 'paraphrased_desc': 'Coagulation factor assay, each factor', 'short_desc': ''},
        {'code': '85397', 'category': 'Laboratory', 'paraphrased_desc': 'Coagulation inhibitor screen', 'short_desc': ''},
        {'code': '85400', 'category': 'Laboratory', 'paraphrased_desc': 'Fibrinolytic factor assay', 'short_desc': ''},
        {'code': '85415', 'category': 'Laboratory', 'paraphrased_desc': 'Plasminogen antigen', 'short_desc': ''},
        {'code': '85420', 'category': 'Laboratory', 'paraphrased_desc': 'Plasminogen activity', 'short_desc': ''},
        {'code': '85421', 'category': 'Laboratory', 'paraphrased_desc': 'Plasminogen activator inhibitor-1', 'short_desc': ''},
    ])

    # EXPANSION: Blood Gas Analysis
    codes.extend([
        {'code': '82803', 'category': 'Laboratory', 'paraphrased_desc': 'Blood gases, arterial, pH, pCO2, pO2', 'short_desc': ''},
        {'code': '82805', 'category': 'Laboratory', 'paraphrased_desc': 'Blood gases, arterial, with O2 saturation', 'short_desc': ''},
        {'code': '82810', 'category': 'Laboratory', 'paraphrased_desc': 'Blood gases, venous', 'short_desc': ''},
        {'code': '82820', 'category': 'Laboratory', 'paraphrased_desc': 'Hemoglobin oxygen affinity', 'short_desc': ''},
    ])

    # EXPANSION: Additional Immunology Tests
    codes.extend([
        {'code': '86038', 'category': 'Laboratory', 'paraphrased_desc': 'Antinuclear antibodies (ANA), titer', 'short_desc': ''},
        {'code': '86039', 'category': 'Laboratory', 'paraphrased_desc': 'Antinuclear antibodies (ANA), pattern', 'short_desc': ''},
        {'code': '86140', 'category': 'Laboratory', 'paraphrased_desc': 'C-reactive protein (CRP)', 'short_desc': ''},
        {'code': '86141', 'category': 'Laboratory', 'paraphrased_desc': 'C-reactive protein (CRP), high sensitivity', 'short_desc': ''},
        {'code': '86430', 'category': 'Laboratory', 'paraphrased_desc': 'Rheumatoid factor, qualitative', 'short_desc': ''},
        {'code': '86431', 'category': 'Laboratory', 'paraphrased_desc': 'Rheumatoid factor, quantitative', 'short_desc': ''},
        {'code': '86200', 'category': 'Laboratory', 'paraphrased_desc': 'Cyclic citrullinated peptide (CCP) antibody', 'short_desc': ''},
        {'code': '86235', 'category': 'Laboratory', 'paraphrased_desc': 'Anti-DNA antibody', 'short_desc': ''},
        {'code': '86255', 'category': 'Laboratory', 'paraphrased_desc': 'Fluorescent antibody screen', 'short_desc': ''},
        {'code': '86160', 'category': 'Laboratory', 'paraphrased_desc': 'Complement C3', 'short_desc': ''},
        {'code': '86161', 'category': 'Laboratory', 'paraphrased_desc': 'Complement C4', 'short_desc': ''},
        {'code': '86162', 'category': 'Laboratory', 'paraphrased_desc': 'Complement total (CH50)', 'short_desc': ''},
        {'code': '82784', 'category': 'Laboratory', 'paraphrased_desc': 'IgA (immunoglobulin A)', 'short_desc': ''},
        {'code': '82787', 'category': 'Laboratory', 'paraphrased_desc': 'IgE (immunoglobulin E)', 'short_desc': ''},
        {'code': '82785', 'category': 'Laboratory', 'paraphrased_desc': 'IgG (immunoglobulin G)', 'short_desc': ''},
        {'code': '82784', 'category': 'Laboratory', 'paraphrased_desc': 'IgM (immunoglobulin M)', 'short_desc': ''},
        {'code': '86334', 'category': 'Laboratory', 'paraphrased_desc': 'Immunofixation electrophoresis, serum', 'short_desc': ''},
        {'code': '86335', 'category': 'Laboratory', 'paraphrased_desc': 'Immunofixation electrophoresis, other fluids', 'short_desc': ''},
    ])

    # EXPANSION: Infectious Disease Serology
    codes.extend([
        {'code': '86701', 'category': 'Laboratory', 'paraphrased_desc': 'HIV-1 antibody test', 'short_desc': ''},
        {'code': '86702', 'category': 'Laboratory', 'paraphrased_desc': 'HIV-1 and HIV-2, single assay', 'short_desc': ''},
        {'code': '86703', 'category': 'Laboratory', 'paraphrased_desc': 'HIV-1 antibody, confirmatory test', 'short_desc': ''},
        {'code': '87389', 'category': 'Laboratory', 'paraphrased_desc': 'HIV-1 antigen detection', 'short_desc': ''},
        {'code': '86704', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis B core antibody (anti-HBc), total', 'short_desc': ''},
        {'code': '86705', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis B core antibody (anti-HBc), IgM', 'short_desc': ''},
        {'code': '87340', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis B surface antigen (HBsAg)', 'short_desc': ''},
        {'code': '86706', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis B surface antibody (anti-HBs)', 'short_desc': ''},
        {'code': '87350', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis Be antigen (HBeAg)', 'short_desc': ''},
        {'code': '86707', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis Be antibody (anti-HBe)', 'short_desc': ''},
        {'code': '86803', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis C antibody', 'short_desc': ''},
        {'code': '86804', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis C antibody, confirmatory', 'short_desc': ''},
        {'code': '87520', 'category': 'Laboratory', 'paraphrased_desc': 'Hepatitis C virus, direct probe', 'short_desc': ''},
        {'code': '86780', 'category': 'Laboratory', 'paraphrased_desc': 'Treponema pallidum antibody (syphilis)', 'short_desc': ''},
        {'code': '86592', 'category': 'Laboratory', 'paraphrased_desc': 'Syphilis, non-treponemal antibody (RPR)', 'short_desc': ''},
        {'code': '86593', 'category': 'Laboratory', 'paraphrased_desc': 'Syphilis, non-treponemal antibody (VDRL)', 'short_desc': ''},
        {'code': '86617', 'category': 'Laboratory', 'paraphrased_desc': 'Lyme disease antibody (Borrelia)', 'short_desc': ''},
        {'code': '86618', 'category': 'Laboratory', 'paraphrased_desc': 'Lyme disease confirmatory test (Western blot)', 'short_desc': ''},
        {'code': '86762', 'category': 'Laboratory', 'paraphrased_desc': 'Rubella antibody', 'short_desc': ''},
        {'code': '86765', 'category': 'Laboratory', 'paraphrased_desc': 'Rubeola (measles) antibody', 'short_desc': ''},
        {'code': '86644', 'category': 'Laboratory', 'paraphrased_desc': 'Cytomegalovirus (CMV) antibody, IgG', 'short_desc': ''},
        {'code': '86645', 'category': 'Laboratory', 'paraphrased_desc': 'Cytomegalovirus (CMV) antibody, IgM', 'short_desc': ''},
        {'code': '86663', 'category': 'Laboratory', 'paraphrased_desc': 'Epstein-Barr virus (EBV) antibody', 'short_desc': ''},
        {'code': '86694', 'category': 'Laboratory', 'paraphrased_desc': 'Herpes simplex virus, non-specific antibody', 'short_desc': ''},
        {'code': '86695', 'category': 'Laboratory', 'paraphrased_desc': 'Herpes simplex virus, type 1 specific', 'short_desc': ''},
        {'code': '86696', 'category': 'Laboratory', 'paraphrased_desc': 'Herpes simplex virus, type 2 specific', 'short_desc': ''},
        {'code': '86790', 'category': 'Laboratory', 'paraphrased_desc': 'Varicella-zoster virus antibody', 'short_desc': ''},
        {'code': '86580', 'category': 'Laboratory', 'paraphrased_desc': 'Toxoplasma antibody', 'short_desc': ''},
        {'code': '86777', 'category': 'Laboratory', 'paraphrased_desc': 'Toxoplasma antibody, IgG', 'short_desc': ''},
        {'code': '86778', 'category': 'Laboratory', 'paraphrased_desc': 'Toxoplasma antibody, IgM', 'short_desc': ''},
    ])

    # EXPANSION: Genetic/Molecular Tests
    codes.extend([
        {'code': '81211', 'category': 'Laboratory', 'paraphrased_desc': 'BRCA1 and BRCA2 gene analysis, full sequence', 'short_desc': ''},
        {'code': '81212', 'category': 'Laboratory', 'paraphrased_desc': 'BRCA1 gene analysis, 185delAG variant', 'short_desc': ''},
        {'code': '81220', 'category': 'Laboratory', 'paraphrased_desc': 'CFTR gene analysis for cystic fibrosis, common variants', 'short_desc': ''},
        {'code': '81221', 'category': 'Laboratory', 'paraphrased_desc': 'CFTR gene analysis for cystic fibrosis, known familial variants', 'short_desc': ''},
        {'code': '81222', 'category': 'Laboratory', 'paraphrased_desc': 'CFTR gene analysis for cystic fibrosis, full gene sequence', 'short_desc': ''},
        {'code': '81240', 'category': 'Laboratory', 'paraphrased_desc': 'F2 gene analysis, prothrombin mutation', 'short_desc': ''},
        {'code': '81241', 'category': 'Laboratory', 'paraphrased_desc': 'F5 gene analysis, Factor V Leiden mutation', 'short_desc': ''},
        {'code': '81245', 'category': 'Laboratory', 'paraphrased_desc': 'FMR1 gene analysis for Fragile X syndrome', 'short_desc': ''},
        {'code': '81250', 'category': 'Laboratory', 'paraphrased_desc': 'G6PD gene analysis, common variants', 'short_desc': ''},
        {'code': '81257', 'category': 'Laboratory', 'paraphrased_desc': 'HBA1/HBA2 gene analysis for alpha thalassemia', 'short_desc': ''},
        {'code': '81361', 'category': 'Laboratory', 'paraphrased_desc': 'HBB gene analysis for beta hemoglobinopathy', 'short_desc': ''},
        {'code': '81401', 'category': 'Laboratory', 'paraphrased_desc': 'Molecular pathology, Level 2', 'short_desc': ''},
        {'code': '81402', 'category': 'Laboratory', 'paraphrased_desc': 'Molecular pathology, Level 3', 'short_desc': ''},
        {'code': '81403', 'category': 'Laboratory', 'paraphrased_desc': 'Molecular pathology, Level 4', 'short_desc': ''},
        {'code': '81404', 'category': 'Laboratory', 'paraphrased_desc': 'Molecular pathology, Level 5', 'short_desc': ''},
        {'code': '81405', 'category': 'Laboratory', 'paraphrased_desc': 'Molecular pathology, Level 6', 'short_desc': ''},
    ])

    # EXPANSION: Microbiology - Additional Tests
    codes.extend([
        {'code': '87081', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, presumptive pathogenic organisms, screening only', 'short_desc': ''},
        {'code': '87084', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, blood, with organism isolation and sensitivity', 'short_desc': ''},
        {'code': '87101', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, fungi, skin, hair, or nail', 'short_desc': ''},
        {'code': '87102', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, fungi, other source', 'short_desc': ''},
        {'code': '87103', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, fungi, blood', 'short_desc': ''},
        {'code': '87106', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, fungi, definitive identification', 'short_desc': ''},
        {'code': '87116', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, mycobacteria, definitive identification', 'short_desc': ''},
        {'code': '87118', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, mycobacterial, other', 'short_desc': ''},
        {'code': '87140', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, typing, immunologic method', 'short_desc': ''},
        {'code': '87143', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, typing, gas liquid chromatography method', 'short_desc': ''},
        {'code': '87147', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, typing, identification by nucleic acid probe', 'short_desc': ''},
        {'code': '87149', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, typing, identification by nucleic acid sequencing', 'short_desc': ''},
        {'code': '87150', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, typing, identification by pulse field gel electrophoresis', 'short_desc': ''},
        {'code': '87152', 'category': 'Laboratory', 'paraphrased_desc': 'Culture, typing, identification by MALDI-TOF mass spectrometry', 'short_desc': ''},
        {'code': '87153', 'category': 'Laboratory', 'paraphrased_desc': 'Organism identification by nucleic acid probe', 'short_desc': ''},
        {'code': '87158', 'category': 'Laboratory', 'paraphrased_desc': 'Organism identification by nucleic acid sequencing', 'short_desc': ''},
        {'code': '87176', 'category': 'Laboratory', 'paraphrased_desc': 'Homogenization, tissue for culture', 'short_desc': ''},
        {'code': '87177', 'category': 'Laboratory', 'paraphrased_desc': 'Ova and parasites, direct smears', 'short_desc': ''},
        {'code': '87181', 'category': 'Laboratory', 'paraphrased_desc': 'Susceptibility studies, antimicrobial agent, each agent', 'short_desc': ''},
        {'code': '87184', 'category': 'Laboratory', 'paraphrased_desc': 'Susceptibility studies, disk method, per plate', 'short_desc': ''},
        {'code': '87185', 'category': 'Laboratory', 'paraphrased_desc': 'Susceptibility studies, enzyme detection', 'short_desc': ''},
        {'code': '87186', 'category': 'Laboratory', 'paraphrased_desc': 'Susceptibility studies, microdilution or agar dilution', 'short_desc': ''},
        {'code': '87187', 'category': 'Laboratory', 'paraphrased_desc': 'Susceptibility studies, microbial, minimum lethal concentration', 'short_desc': ''},
        {'code': '87188', 'category': 'Laboratory', 'paraphrased_desc': 'Susceptibility studies, macrobroth dilution', 'short_desc': ''},
    ])

    # EXPANSION: Additional Chemistry Tests
    codes.extend([
        {'code': '82108', 'category': 'Laboratory', 'paraphrased_desc': 'Aluminum measurement', 'short_desc': ''},
        {'code': '82131', 'category': 'Laboratory', 'paraphrased_desc': 'Amino acids, single quantitative', 'short_desc': ''},
        {'code': '82135', 'category': 'Laboratory', 'paraphrased_desc': 'Aminolevulinic acid (ALA)', 'short_desc': ''},
        {'code': '82139', 'category': 'Laboratory', 'paraphrased_desc': 'Ammonia measurement', 'short_desc': ''},
        {'code': '82150', 'category': 'Laboratory', 'paraphrased_desc': 'Amylase measurement', 'short_desc': ''},
        {'code': '82232', 'category': 'Laboratory', 'paraphrased_desc': 'Beta-2 microglobulin', 'short_desc': ''},
        {'code': '82300', 'category': 'Laboratory', 'paraphrased_desc': 'Cadmium measurement', 'short_desc': ''},
        {'code': '82308', 'category': 'Laboratory', 'paraphrased_desc': 'Calcitonin measurement', 'short_desc': ''},
        {'code': '82330', 'category': 'Laboratory', 'paraphrased_desc': 'Calcium, ionized', 'short_desc': ''},
        {'code': '82340', 'category': 'Laboratory', 'paraphrased_desc': 'Calcium, urine quantitative', 'short_desc': ''},
        {'code': '82355', 'category': 'Laboratory', 'paraphrased_desc': 'Calculus (stone) analysis, qualitative', 'short_desc': ''},
        {'code': '82360', 'category': 'Laboratory', 'paraphrased_desc': 'Calculus (stone) analysis, quantitative', 'short_desc': ''},
        {'code': '82365', 'category': 'Laboratory', 'paraphrased_desc': 'Calculus (stone) analysis, infrared spectroscopy', 'short_desc': ''},
        {'code': '82373', 'category': 'Laboratory', 'paraphrased_desc': 'Carbohydrate deficient transferrin', 'short_desc': ''},
        {'code': '82379', 'category': 'Laboratory', 'paraphrased_desc': 'Carnitine, total and free', 'short_desc': ''},
        {'code': '82380', 'category': 'Laboratory', 'paraphrased_desc': 'Carotene measurement', 'short_desc': ''},
        {'code': '82382', 'category': 'Laboratory', 'paraphrased_desc': 'Catecholamines, total urine', 'short_desc': ''},
        {'code': '82383', 'category': 'Laboratory', 'paraphrased_desc': 'Catecholamines, blood', 'short_desc': ''},
        {'code': '82384', 'category': 'Laboratory', 'paraphrased_desc': 'Catecholamines, fractionated', 'short_desc': ''},
        {'code': '82387', 'category': 'Laboratory', 'paraphrased_desc': 'Cathepsin-D', 'short_desc': ''},
        {'code': '82390', 'category': 'Laboratory', 'paraphrased_desc': 'Ceruloplasmin measurement', 'short_desc': ''},
        {'code': '82397', 'category': 'Laboratory', 'paraphrased_desc': 'Chemiluminescent assay', 'short_desc': ''},
        {'code': '82415', 'category': 'Laboratory', 'paraphrased_desc': 'Chloramphenicol level', 'short_desc': ''},
        {'code': '82436', 'category': 'Laboratory', 'paraphrased_desc': 'Chloride, urine', 'short_desc': ''},
        {'code': '82438', 'category': 'Laboratory', 'paraphrased_desc': 'Chloride, other source', 'short_desc': ''},
    ])

    logger.info(f"Generated {len(codes)} Laboratory codes")
    return codes


def generate_radiology_codes() -> List[Dict]:
    """Generate common Radiology codes 70000-79999

    Expanded to ~350 codes covering comprehensive imaging procedures.
    """
    codes = []

    # X-rays - Chest (71045-71048)
    codes.extend([
        {'code': '71045', 'category': 'Radiology', 'paraphrased_desc': 'Chest X-ray, single view', 'short_desc': ''},
        {'code': '71046', 'category': 'Radiology', 'paraphrased_desc': 'Chest X-ray, 2 views', 'short_desc': ''},
        {'code': '71047', 'category': 'Radiology', 'paraphrased_desc': 'Chest X-ray, 3 views', 'short_desc': ''},
        {'code': '71048', 'category': 'Radiology', 'paraphrased_desc': 'Chest X-ray, 4 or more views', 'short_desc': ''},
    ])

    # X-rays - Spine
    codes.extend([
        {'code': '72020', 'category': 'Radiology', 'paraphrased_desc': 'Spine X-ray, single view', 'short_desc': ''},
        {'code': '72040', 'category': 'Radiology', 'paraphrased_desc': 'Cervical spine X-ray, 2-3 views', 'short_desc': ''},
        {'code': '72050', 'category': 'Radiology', 'paraphrased_desc': 'Cervical spine X-ray, complete 4-5 views', 'short_desc': ''},
        {'code': '72070', 'category': 'Radiology', 'paraphrased_desc': 'Thoracic spine X-ray, 2 views', 'short_desc': ''},
        {'code': '72072', 'category': 'Radiology', 'paraphrased_desc': 'Thoracic spine X-ray, 3 views', 'short_desc': ''},
        {'code': '72100', 'category': 'Radiology', 'paraphrased_desc': 'Lumbar spine X-ray, 2-3 views', 'short_desc': ''},
        {'code': '72110', 'category': 'Radiology', 'paraphrased_desc': 'Lumbar spine X-ray, complete 4-5 views', 'short_desc': ''},
    ])

    # X-rays - Extremities
    codes.extend([
        {'code': '73000', 'category': 'Radiology', 'paraphrased_desc': 'Clavicle X-ray', 'short_desc': ''},
        {'code': '73010', 'category': 'Radiology', 'paraphrased_desc': 'Scapula X-ray', 'short_desc': ''},
        {'code': '73020', 'category': 'Radiology', 'paraphrased_desc': 'Shoulder X-ray, single view', 'short_desc': ''},
        {'code': '73030', 'category': 'Radiology', 'paraphrased_desc': 'Shoulder X-ray, complete', 'short_desc': ''},
        {'code': '73060', 'category': 'Radiology', 'paraphrased_desc': 'Humerus X-ray', 'short_desc': ''},
        {'code': '73070', 'category': 'Radiology', 'paraphrased_desc': 'Elbow X-ray, 2 views', 'short_desc': ''},
        {'code': '73080', 'category': 'Radiology', 'paraphrased_desc': 'Elbow X-ray, complete', 'short_desc': ''},
        {'code': '73090', 'category': 'Radiology', 'paraphrased_desc': 'Forearm X-ray, 2 views', 'short_desc': ''},
        {'code': '73100', 'category': 'Radiology', 'paraphrased_desc': 'Wrist X-ray, 2 views', 'short_desc': ''},
        {'code': '73110', 'category': 'Radiology', 'paraphrased_desc': 'Wrist X-ray, complete', 'short_desc': ''},
        {'code': '73120', 'category': 'Radiology', 'paraphrased_desc': 'Hand X-ray, 2 views', 'short_desc': ''},
        {'code': '73130', 'category': 'Radiology', 'paraphrased_desc': 'Hand X-ray, complete 3 views', 'short_desc': ''},
        {'code': '73140', 'category': 'Radiology', 'paraphrased_desc': 'Finger X-ray', 'short_desc': ''},
    ])

    # X-rays - Lower extremities
    codes.extend([
        {'code': '73500', 'category': 'Radiology', 'paraphrased_desc': 'Hip X-ray, single view', 'short_desc': ''},
        {'code': '73510', 'category': 'Radiology', 'paraphrased_desc': 'Hip X-ray, complete', 'short_desc': ''},
        {'code': '73520', 'category': 'Radiology', 'paraphrased_desc': 'Hips bilateral X-ray, 2-3 views', 'short_desc': ''},
        {'code': '73550', 'category': 'Radiology', 'paraphrased_desc': 'Femur X-ray', 'short_desc': ''},
        {'code': '73560', 'category': 'Radiology', 'paraphrased_desc': 'Knee X-ray, 1-2 views', 'short_desc': ''},
        {'code': '73562', 'category': 'Radiology', 'paraphrased_desc': 'Knee X-ray, 3 views', 'short_desc': ''},
        {'code': '73564', 'category': 'Radiology', 'paraphrased_desc': 'Knee X-ray, complete 4 or more views', 'short_desc': ''},
        {'code': '73590', 'category': 'Radiology', 'paraphrased_desc': 'Tibia and fibula X-ray, 2 views', 'short_desc': ''},
        {'code': '73600', 'category': 'Radiology', 'paraphrased_desc': 'Ankle X-ray, 2 views', 'short_desc': ''},
        {'code': '73610', 'category': 'Radiology', 'paraphrased_desc': 'Ankle X-ray, complete 3 views', 'short_desc': ''},
        {'code': '73620', 'category': 'Radiology', 'paraphrased_desc': 'Foot X-ray, 2 views', 'short_desc': ''},
        {'code': '73630', 'category': 'Radiology', 'paraphrased_desc': 'Foot X-ray, complete 3 views', 'short_desc': ''},
        {'code': '73650', 'category': 'Radiology', 'paraphrased_desc': 'Heel (calcaneus) X-ray', 'short_desc': ''},
        {'code': '73660', 'category': 'Radiology', 'paraphrased_desc': 'Toe X-ray', 'short_desc': ''},
    ])

    # CT scans - Head/Brain
    codes.extend([
        {'code': '70450', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of head or brain without contrast', 'short_desc': ''},
        {'code': '70460', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of head or brain with contrast', 'short_desc': ''},
        {'code': '70470', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of head or brain without contrast, followed by with contrast', 'short_desc': ''},
    ])

    # CT scans - Chest
    codes.extend([
        {'code': '71250', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of chest without contrast', 'short_desc': ''},
        {'code': '71260', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of chest with contrast', 'short_desc': ''},
        {'code': '71270', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of chest without contrast, followed by with contrast', 'short_desc': ''},
    ])

    # CT scans - Abdomen
    codes.extend([
        {'code': '74150', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of abdomen without contrast', 'short_desc': ''},
        {'code': '74160', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of abdomen with contrast', 'short_desc': ''},
        {'code': '74170', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of abdomen without contrast, followed by with contrast', 'short_desc': ''},
    ])

    # CT scans - Pelvis
    codes.extend([
        {'code': '72192', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of pelvis without contrast', 'short_desc': ''},
        {'code': '72193', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of pelvis with contrast', 'short_desc': ''},
        {'code': '72194', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of pelvis without contrast, followed by with contrast', 'short_desc': ''},
    ])

    # CT scans - Abdomen and pelvis combined
    codes.extend([
        {'code': '74176', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of abdomen and pelvis without contrast', 'short_desc': ''},
        {'code': '74177', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of abdomen and pelvis with contrast', 'short_desc': ''},
        {'code': '74178', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of abdomen and pelvis without contrast, followed by with contrast', 'short_desc': ''},
    ])

    # MRI - Brain
    codes.extend([
        {'code': '70551', 'category': 'Radiology', 'paraphrased_desc': 'MRI of brain without contrast', 'short_desc': ''},
        {'code': '70552', 'category': 'Radiology', 'paraphrased_desc': 'MRI of brain with contrast', 'short_desc': ''},
        {'code': '70553', 'category': 'Radiology', 'paraphrased_desc': 'MRI of brain without contrast, followed by with contrast', 'short_desc': ''},
    ])

    # MRI - Spine
    codes.extend([
        {'code': '72141', 'category': 'Radiology', 'paraphrased_desc': 'MRI of cervical spine without contrast', 'short_desc': ''},
        {'code': '72142', 'category': 'Radiology', 'paraphrased_desc': 'MRI of cervical spine with contrast', 'short_desc': ''},
        {'code': '72146', 'category': 'Radiology', 'paraphrased_desc': 'MRI of thoracic spine without contrast', 'short_desc': ''},
        {'code': '72148', 'category': 'Radiology', 'paraphrased_desc': 'MRI of lumbar spine without contrast', 'short_desc': ''},
        {'code': '72149', 'category': 'Radiology', 'paraphrased_desc': 'MRI of lumbar spine with contrast', 'short_desc': ''},
    ])

    # MRI - Joints
    codes.extend([
        {'code': '73221', 'category': 'Radiology', 'paraphrased_desc': 'MRI of any joint of upper extremity without contrast', 'short_desc': ''},
        {'code': '73721', 'category': 'Radiology', 'paraphrased_desc': 'MRI of any joint of lower extremity without contrast', 'short_desc': ''},
    ])

    # Ultrasound - Abdomen
    codes.extend([
        {'code': '76700', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound of abdomen, complete', 'short_desc': ''},
        {'code': '76705', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound of abdomen, limited', 'short_desc': ''},
    ])

    # Ultrasound - Pelvis
    codes.extend([
        {'code': '76856', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound of pelvis (non-obstetric), complete', 'short_desc': ''},
        {'code': '76857', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound of pelvis (non-obstetric), limited', 'short_desc': ''},
    ])

    # Ultrasound - Pregnancy
    codes.extend([
        {'code': '76801', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, pregnant uterus, first trimester, single fetus', 'short_desc': ''},
        {'code': '76805', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, pregnant uterus, after first trimester, single fetus', 'short_desc': ''},
        {'code': '76811', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, pregnant uterus, detailed fetal anatomic exam, single fetus', 'short_desc': ''},
        {'code': '76815', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, pregnant uterus, limited exam', 'short_desc': ''},
        {'code': '76817', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, pregnant uterus, transvaginal', 'short_desc': ''},
    ])

    # Ultrasound - Vascular
    codes.extend([
        {'code': '93880', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound study of arteries in head and neck', 'short_desc': ''},
        {'code': '93970', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound study of veins in extremities', 'short_desc': ''},
        {'code': '93971', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound study of veins in extremities, unilateral or limited', 'short_desc': ''},
    ])

    # Mammography
    codes.extend([
        {'code': '77065', 'category': 'Radiology', 'paraphrased_desc': 'Screening mammography, bilateral, 2D digital', 'short_desc': ''},
        {'code': '77066', 'category': 'Radiology', 'paraphrased_desc': 'Diagnostic mammography, unilateral', 'short_desc': ''},
        {'code': '77067', 'category': 'Radiology', 'paraphrased_desc': 'Diagnostic mammography, bilateral', 'short_desc': ''},
    ])

    # DEXA scan (77080)
    codes.append({
        'code': '77080',
        'category': 'Radiology',
        'paraphrased_desc': 'Bone density study (DEXA scan) for osteoporosis screening',
        'short_desc': '',
    })

    # Nuclear medicine
    codes.extend([
        {'code': '78306', 'category': 'Radiology', 'paraphrased_desc': 'Bone scan, whole body', 'short_desc': ''},
        {'code': '78452', 'category': 'Radiology', 'paraphrased_desc': 'Heart muscle imaging (myocardial perfusion), multiple studies', 'short_desc': ''},
        {'code': '78465', 'category': 'Radiology', 'paraphrased_desc': 'Heart muscle blood flow imaging at rest and stress', 'short_desc': ''},
    ])

    # EXPANSION: Additional X-rays
    codes.extend([
        {'code': '70030', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of eye for foreign body', 'short_desc': ''},
        {'code': '70100', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of jaw, mandible', 'short_desc': ''},
        {'code': '70110', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of jaw, mandible, complete', 'short_desc': ''},
        {'code': '70120', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of mastoids', 'short_desc': ''},
        {'code': '70130', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of mastoids, complete series', 'short_desc': ''},
        {'code': '70140', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of facial bones, less than 3 views', 'short_desc': ''},
        {'code': '70150', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of facial bones, complete', 'short_desc': ''},
        {'code': '70160', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of nasal bones', 'short_desc': ''},
        {'code': '70170', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of tear duct (dacryocystography)', 'short_desc': ''},
        {'code': '70190', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of eye sockets (orbits)', 'short_desc': ''},
        {'code': '70200', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of eye sockets (orbits), complete', 'short_desc': ''},
        {'code': '70210', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of sinuses, less than 3 views', 'short_desc': ''},
        {'code': '70220', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of sinuses, complete', 'short_desc': ''},
        {'code': '70250', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of skull, less than 4 views', 'short_desc': ''},
        {'code': '70260', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of skull, complete', 'short_desc': ''},
        {'code': '70360', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of neck, soft tissue', 'short_desc': ''},
        {'code': '70380', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of salivary gland for stones', 'short_desc': ''},
        {'code': '72170', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of pelvis, 1-2 views', 'short_desc': ''},
        {'code': '72190', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of pelvis, complete', 'short_desc': ''},
        {'code': '72200', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of sacroiliac joints, less than 3 views', 'short_desc': ''},
        {'code': '72202', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of sacroiliac joints, 3 or more views', 'short_desc': ''},
        {'code': '72220', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of sacrum and coccyx, 2 views', 'short_desc': ''},
        {'code': '73090', 'category': 'Radiology', 'paraphrased_desc': 'X-ray of forearm, 2 views', 'short_desc': ''},
        {'code': '73200', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of upper extremity without contrast', 'short_desc': ''},
        {'code': '73201', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of upper extremity with contrast', 'short_desc': ''},
        {'code': '73202', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of upper extremity without and with contrast', 'short_desc': ''},
        {'code': '73700', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of lower extremity without contrast', 'short_desc': ''},
        {'code': '73701', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of lower extremity with contrast', 'short_desc': ''},
        {'code': '73702', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of lower extremity without and with contrast', 'short_desc': ''},
        {'code': '72125', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of cervical spine without contrast', 'short_desc': ''},
        {'code': '72126', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of cervical spine with contrast', 'short_desc': ''},
        {'code': '72127', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of cervical spine without and with contrast', 'short_desc': ''},
        {'code': '72128', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of thoracic spine without contrast', 'short_desc': ''},
        {'code': '72129', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of thoracic spine with contrast', 'short_desc': ''},
        {'code': '72130', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of thoracic spine without and with contrast', 'short_desc': ''},
        {'code': '72131', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of lumbar spine without contrast', 'short_desc': ''},
        {'code': '72132', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of lumbar spine with contrast', 'short_desc': ''},
        {'code': '72133', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of lumbar spine without and with contrast', 'short_desc': ''},
        {'code': '70480', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of orbits, ear or fossa without contrast', 'short_desc': ''},
        {'code': '70481', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of orbits, ear or fossa with contrast', 'short_desc': ''},
        {'code': '70482', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of orbits, ear or fossa without and with contrast', 'short_desc': ''},
        {'code': '70486', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of maxillofacial area without contrast', 'short_desc': ''},
        {'code': '70487', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of maxillofacial area with contrast', 'short_desc': ''},
        {'code': '70488', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of maxillofacial area without and with contrast', 'short_desc': ''},
        {'code': '70490', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of soft tissue of neck without contrast', 'short_desc': ''},
        {'code': '70491', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of soft tissue of neck with contrast', 'short_desc': ''},
        {'code': '70492', 'category': 'Radiology', 'paraphrased_desc': 'CT scan of soft tissue of neck without and with contrast', 'short_desc': ''},
    ])

    # EXPANSION: Additional MRI
    codes.extend([
        {'code': '70540', 'category': 'Radiology', 'paraphrased_desc': 'MRI of orbit, face, or neck without contrast', 'short_desc': ''},
        {'code': '70542', 'category': 'Radiology', 'paraphrased_desc': 'MRI of orbit, face, or neck with contrast', 'short_desc': ''},
        {'code': '70543', 'category': 'Radiology', 'paraphrased_desc': 'MRI of orbit, face, or neck without and with contrast', 'short_desc': ''},
        {'code': '70544', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of head without contrast', 'short_desc': ''},
        {'code': '70545', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of head with contrast', 'short_desc': ''},
        {'code': '70546', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of head without and with contrast', 'short_desc': ''},
        {'code': '70547', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of neck without contrast', 'short_desc': ''},
        {'code': '70548', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of neck with contrast', 'short_desc': ''},
        {'code': '70549', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of neck without and with contrast', 'short_desc': ''},
        {'code': '71550', 'category': 'Radiology', 'paraphrased_desc': 'MRI of chest without contrast', 'short_desc': ''},
        {'code': '71551', 'category': 'Radiology', 'paraphrased_desc': 'MRI of chest with contrast', 'short_desc': ''},
        {'code': '71552', 'category': 'Radiology', 'paraphrased_desc': 'MRI of chest without and with contrast', 'short_desc': ''},
        {'code': '71555', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of chest without contrast', 'short_desc': ''},
        {'code': '72195', 'category': 'Radiology', 'paraphrased_desc': 'MRI of pelvis without contrast', 'short_desc': ''},
        {'code': '72196', 'category': 'Radiology', 'paraphrased_desc': 'MRI of pelvis with contrast', 'short_desc': ''},
        {'code': '72197', 'category': 'Radiology', 'paraphrased_desc': 'MRI of pelvis without and with contrast', 'short_desc': ''},
        {'code': '72198', 'category': 'Radiology', 'paraphrased_desc': 'MRI of pelvis without contrast, repeat or limited study', 'short_desc': ''},
        {'code': '73218', 'category': 'Radiology', 'paraphrased_desc': 'MRI of upper extremity without contrast', 'short_desc': ''},
        {'code': '73219', 'category': 'Radiology', 'paraphrased_desc': 'MRI of upper extremity with contrast', 'short_desc': ''},
        {'code': '73220', 'category': 'Radiology', 'paraphrased_desc': 'MRI of upper extremity without and with contrast', 'short_desc': ''},
        {'code': '73718', 'category': 'Radiology', 'paraphrased_desc': 'MRI of lower extremity without contrast', 'short_desc': ''},
        {'code': '73719', 'category': 'Radiology', 'paraphrased_desc': 'MRI of lower extremity with contrast', 'short_desc': ''},
        {'code': '73720', 'category': 'Radiology', 'paraphrased_desc': 'MRI of lower extremity without and with contrast', 'short_desc': ''},
        {'code': '74181', 'category': 'Radiology', 'paraphrased_desc': 'MRI of abdomen without contrast', 'short_desc': ''},
        {'code': '74182', 'category': 'Radiology', 'paraphrased_desc': 'MRI of abdomen with contrast', 'short_desc': ''},
        {'code': '74183', 'category': 'Radiology', 'paraphrased_desc': 'MRI of abdomen without and with contrast', 'short_desc': ''},
        {'code': '74185', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of abdomen without contrast', 'short_desc': ''},
        {'code': '74187', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of abdomen with contrast', 'short_desc': ''},
        {'code': '73225', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of upper extremity', 'short_desc': ''},
        {'code': '73725', 'category': 'Radiology', 'paraphrased_desc': 'MRA (angiography) of lower extremity', 'short_desc': ''},
    ])

    # EXPANSION: Fluoroscopy and Contrast Studies
    codes.extend([
        {'code': '74210', 'category': 'Radiology', 'paraphrased_desc': 'Contrast X-ray of esophagus', 'short_desc': ''},
        {'code': '74220', 'category': 'Radiology', 'paraphrased_desc': 'Contrast X-ray of esophagus, multiple studies', 'short_desc': ''},
        {'code': '74230', 'category': 'Radiology', 'paraphrased_desc': 'Barium swallow study', 'short_desc': ''},
        {'code': '74240', 'category': 'Radiology', 'paraphrased_desc': 'Upper GI series with films', 'short_desc': ''},
        {'code': '74245', 'category': 'Radiology', 'paraphrased_desc': 'Upper GI series with air contrast', 'short_desc': ''},
        {'code': '74246', 'category': 'Radiology', 'paraphrased_desc': 'Upper GI series, radiological supervision', 'short_desc': ''},
        {'code': '74247', 'category': 'Radiology', 'paraphrased_desc': 'Upper GI series with air contrast, radiological supervision', 'short_desc': ''},
        {'code': '74249', 'category': 'Radiology', 'paraphrased_desc': 'Upper GI tract X-ray and small bowel', 'short_desc': ''},
        {'code': '74250', 'category': 'Radiology', 'paraphrased_desc': 'Small bowel X-ray series', 'short_desc': ''},
        {'code': '74251', 'category': 'Radiology', 'paraphrased_desc': 'Small bowel X-ray series with timed films', 'short_desc': ''},
        {'code': '74270', 'category': 'Radiology', 'paraphrased_desc': 'Barium enema with air contrast', 'short_desc': ''},
        {'code': '74280', 'category': 'Radiology', 'paraphrased_desc': 'Barium enema with air contrast, with fluoroscopy', 'short_desc': ''},
        {'code': '76000', 'category': 'Radiology', 'paraphrased_desc': 'Fluoroscopy, up to 1 hour', 'short_desc': ''},
        {'code': '76001', 'category': 'Radiology', 'paraphrased_desc': 'Fluoroscopy, over 1 hour', 'short_desc': ''},
        {'code': '76010', 'category': 'Radiology', 'paraphrased_desc': 'Radiologic examination from nose to rectum for foreign body', 'short_desc': ''},
    ])

    # EXPANSION: Additional Nuclear Medicine
    codes.extend([
        {'code': '78300', 'category': 'Radiology', 'paraphrased_desc': 'Bone scan, limited area', 'short_desc': ''},
        {'code': '78305', 'category': 'Radiology', 'paraphrased_desc': 'Bone scan, multiple areas', 'short_desc': ''},
        {'code': '78315', 'category': 'Radiology', 'paraphrased_desc': 'Bone scan, 3-phase study', 'short_desc': ''},
        {'code': '78320', 'category': 'Radiology', 'paraphrased_desc': 'Bone scan, tomographic (SPECT)', 'short_desc': ''},
        {'code': '78350', 'category': 'Radiology', 'paraphrased_desc': 'Bone density measurement, single site', 'short_desc': ''},
        {'code': '78351', 'category': 'Radiology', 'paraphrased_desc': 'Bone density measurement, multiple sites', 'short_desc': ''},
        {'code': '78428', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac shunt detection', 'short_desc': ''},
        {'code': '78430', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac blood pool imaging, gated equilibrium', 'short_desc': ''},
        {'code': '78433', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac blood pool imaging, first pass', 'short_desc': ''},
        {'code': '78445', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac blood pool imaging, special processing', 'short_desc': ''},
        {'code': '78451', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial perfusion imaging, single study', 'short_desc': ''},
        {'code': '78454', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial perfusion imaging, multiple studies', 'short_desc': ''},
        {'code': '78456', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial perfusion imaging, rest and stress', 'short_desc': ''},
        {'code': '78457', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial perfusion imaging, pharmacological stress', 'short_desc': ''},
        {'code': '78458', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial perfusion imaging, exercise and pharmacological stress', 'short_desc': ''},
        {'code': '78459', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial imaging, PET scan, rest and stress', 'short_desc': ''},
        {'code': '78466', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial imaging, PET scan, metabolic evaluation', 'short_desc': ''},
        {'code': '78468', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial imaging, PET scan, single study', 'short_desc': ''},
        {'code': '78469', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial imaging, PET scan, multiple studies', 'short_desc': ''},
        {'code': '78472', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac blood pool imaging, gated equilibrium', 'short_desc': ''},
        {'code': '78473', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac blood pool imaging, multiple studies', 'short_desc': ''},
        {'code': '78481', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac blood pool imaging, first pass', 'short_desc': ''},
        {'code': '78483', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac blood pool imaging, SPECT', 'short_desc': ''},
        {'code': '78491', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial imaging, PET scan, perfusion study', 'short_desc': ''},
        {'code': '78492', 'category': 'Radiology', 'paraphrased_desc': 'Myocardial imaging, PET scan, perfusion and metabolism', 'short_desc': ''},
        {'code': '78496', 'category': 'Radiology', 'paraphrased_desc': 'Cardiac PET scan, absolute quantification', 'short_desc': ''},
        {'code': '78600', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, less than 4 views', 'short_desc': ''},
        {'code': '78601', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, complete study', 'short_desc': ''},
        {'code': '78605', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, vascular flow', 'short_desc': ''},
        {'code': '78606', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, PET scan', 'short_desc': ''},
        {'code': '78607', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, SPECT', 'short_desc': ''},
        {'code': '78608', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, PET scan with CT', 'short_desc': ''},
        {'code': '78609', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, PET scan, limited study', 'short_desc': ''},
        {'code': '78610', 'category': 'Radiology', 'paraphrased_desc': 'Brain imaging, vascular flow only', 'short_desc': ''},
        {'code': '78630', 'category': 'Radiology', 'paraphrased_desc': 'Cerebrospinal fluid scan', 'short_desc': ''},
        {'code': '78635', 'category': 'Radiology', 'paraphrased_desc': 'Cerebrospinal fluid scan, ventriculography', 'short_desc': ''},
        {'code': '78645', 'category': 'Radiology', 'paraphrased_desc': 'Cerebrospinal fluid scan, shunt evaluation', 'short_desc': ''},
        {'code': '78650', 'category': 'Radiology', 'paraphrased_desc': 'Cerebrospinal fluid scan, cisternography', 'short_desc': ''},
        {'code': '78660', 'category': 'Radiology', 'paraphrased_desc': 'Radiopharmaceutical dacryocystography', 'short_desc': ''},
        {'code': '78700', 'category': 'Radiology', 'paraphrased_desc': 'Kidney imaging, morphology', 'short_desc': ''},
        {'code': '78701', 'category': 'Radiology', 'paraphrased_desc': 'Kidney imaging, vascular flow', 'short_desc': ''},
        {'code': '78707', 'category': 'Radiology', 'paraphrased_desc': 'Kidney imaging, SPECT with CT', 'short_desc': ''},
        {'code': '78708', 'category': 'Radiology', 'paraphrased_desc': 'Kidney imaging, SPECT', 'short_desc': ''},
        {'code': '78709', 'category': 'Radiology', 'paraphrased_desc': 'Kidney imaging, SPECT with vascular flow', 'short_desc': ''},
        {'code': '78710', 'category': 'Radiology', 'paraphrased_desc': 'Kidney imaging, vascular flow and function', 'short_desc': ''},
        {'code': '78725', 'category': 'Radiology', 'paraphrased_desc': 'Kidney imaging, function study', 'short_desc': ''},
        {'code': '78730', 'category': 'Radiology', 'paraphrased_desc': 'Urinary bladder residual study', 'short_desc': ''},
        {'code': '78740', 'category': 'Radiology', 'paraphrased_desc': 'Ureteral reflux study', 'short_desc': ''},
        {'code': '78761', 'category': 'Radiology', 'paraphrased_desc': 'Testicular imaging with vascular flow', 'short_desc': ''},
    ])

    # EXPANSION: Angiography
    codes.extend([
        {'code': '75600', 'category': 'Radiology', 'paraphrased_desc': 'Aortography, thoracic', 'short_desc': ''},
        {'code': '75605', 'category': 'Radiology', 'paraphrased_desc': 'Aortography, thoracic, by serialography', 'short_desc': ''},
        {'code': '75625', 'category': 'Radiology', 'paraphrased_desc': 'Aortography, abdominal', 'short_desc': ''},
        {'code': '75630', 'category': 'Radiology', 'paraphrased_desc': 'Aortography, abdominal plus bilateral leg arteries', 'short_desc': ''},
        {'code': '75635', 'category': 'Radiology', 'paraphrased_desc': 'CT angiography of abdominal aorta and bilateral legs', 'short_desc': ''},
        {'code': '75710', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, extremity, unilateral', 'short_desc': ''},
        {'code': '75716', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, extremity, bilateral', 'short_desc': ''},
        {'code': '75726', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, visceral, selective or supraselective', 'short_desc': ''},
        {'code': '75731', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, adrenal, unilateral', 'short_desc': ''},
        {'code': '75733', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, adrenal, bilateral', 'short_desc': ''},
        {'code': '75741', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, pulmonary, unilateral', 'short_desc': ''},
        {'code': '75743', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, pulmonary, bilateral', 'short_desc': ''},
        {'code': '75774', 'category': 'Radiology', 'paraphrased_desc': 'Angiography, each additional vessel', 'short_desc': ''},
    ])

    # EXPANSION: Additional Ultrasound
    codes.extend([
        {'code': '76506', 'category': 'Radiology', 'paraphrased_desc': 'Echoencephalography, B-scan', 'short_desc': ''},
        {'code': '76510', 'category': 'Radiology', 'paraphrased_desc': 'Ophthalmic ultrasound, diagnostic, B-scan', 'short_desc': ''},
        {'code': '76511', 'category': 'Radiology', 'paraphrased_desc': 'Ophthalmic ultrasound, quantitative A-scan only', 'short_desc': ''},
        {'code': '76512', 'category': 'Radiology', 'paraphrased_desc': 'Ophthalmic ultrasound, B-scan with quantitative A-scan', 'short_desc': ''},
        {'code': '76513', 'category': 'Radiology', 'paraphrased_desc': 'Ophthalmic ultrasound, anterior segment', 'short_desc': ''},
        {'code': '76514', 'category': 'Radiology', 'paraphrased_desc': 'Ophthalmic ultrasound, corneal pachymetry', 'short_desc': ''},
        {'code': '76516', 'category': 'Radiology', 'paraphrased_desc': 'Ophthalmic biometry by ultrasound', 'short_desc': ''},
        {'code': '76536', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, soft tissues of head and neck', 'short_desc': ''},
        {'code': '76604', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, chest, B-scan', 'short_desc': ''},
        {'code': '76641', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, breast, unilateral, complete', 'short_desc': ''},
        {'code': '76642', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, breast, limited', 'short_desc': ''},
        {'code': '76770', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, retroperitoneal, complete', 'short_desc': ''},
        {'code': '76775', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, retroperitoneal, limited', 'short_desc': ''},
        {'code': '76776', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, transplanted kidney, complete', 'short_desc': ''},
        {'code': '76830', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, transvaginal', 'short_desc': ''},
        {'code': '76831', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, uterus and adnexa, complete', 'short_desc': ''},
        {'code': '76856', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, pelvic, complete', 'short_desc': ''},
        {'code': '76870', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, scrotum and contents', 'short_desc': ''},
        {'code': '76872', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, transrectal', 'short_desc': ''},
        {'code': '76873', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, transrectal, prostate', 'short_desc': ''},
        {'code': '76881', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, extremity, complete', 'short_desc': ''},
        {'code': '76882', 'category': 'Radiology', 'paraphrased_desc': 'Ultrasound, extremity, limited', 'short_desc': ''},
    ])

    logger.info(f"Generated {len(codes)} Radiology codes")
    return codes


def generate_surgery_codes() -> List[Dict]:
    """Generate common Surgery codes 10000-69999

    Expanded to ~400 codes covering comprehensive surgical procedures.
    """
    codes = []

    # Incision and drainage (10060-10061)
    codes.extend([
        {'code': '10060', 'category': 'Surgery', 'paraphrased_desc': 'Drainage of skin abscess, simple or single', 'short_desc': ''},
        {'code': '10061', 'category': 'Surgery', 'paraphrased_desc': 'Drainage of skin abscess, complicated or multiple', 'short_desc': ''},
    ])

    # Skin lesion removal - Benign
    codes.extend([
        {'code': '11042', 'category': 'Surgery', 'paraphrased_desc': 'Debridement of skin, subcutaneous tissue, up to 20 sq cm', 'short_desc': ''},
        {'code': '11043', 'category': 'Surgery', 'paraphrased_desc': 'Debridement of muscle and/or fascia, up to 20 sq cm', 'short_desc': ''},
        {'code': '11044', 'category': 'Surgery', 'paraphrased_desc': 'Debridement of bone, up to 20 sq cm', 'short_desc': ''},
    ])

    # Skin biopsy
    codes.extend([
        {'code': '11102', 'category': 'Surgery', 'paraphrased_desc': 'Skin biopsy, tangential, single lesion', 'short_desc': ''},
        {'code': '11104', 'category': 'Surgery', 'paraphrased_desc': 'Skin biopsy, punch, single lesion', 'short_desc': ''},
        {'code': '11106', 'category': 'Surgery', 'paraphrased_desc': 'Skin biopsy, incisional, single lesion', 'short_desc': ''},
    ])

    # Skin lesion excision - Benign
    for size_code, size in [('0', '0.5 cm or less'), ('1', '0.6-1.0 cm'), ('2', '1.1-2.0 cm'), ('3', '2.1-3.0 cm'), ('4', '3.1-4.0 cm')]:
        codes.append({
            'code': f'1140{size_code}',
            'category': 'Surgery',
            'paraphrased_desc': f'Excision of benign skin lesion, trunk/arms/legs, {size}',
            'short_desc': '',
        })

    # Skin tag removal (11200-11201)
    codes.extend([
        {'code': '11200', 'category': 'Surgery', 'paraphrased_desc': 'Removal of skin tags, up to 15 lesions', 'short_desc': ''},
        {'code': '11201', 'category': 'Surgery', 'paraphrased_desc': 'Removal of skin tags, each additional 10 lesions', 'short_desc': ''},
    ])

    # Skin lesion destruction
    codes.extend([
        {'code': '17000', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of premalignant lesion, first lesion', 'short_desc': ''},
        {'code': '17003', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of premalignant lesion, 2-14 additional lesions', 'short_desc': ''},
        {'code': '17004', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of premalignant lesion, 15 or more lesions', 'short_desc': ''},
        {'code': '17110', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of benign lesions, up to 14 lesions', 'short_desc': ''},
        {'code': '17111', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of benign lesions, 15 or more lesions', 'short_desc': ''},
    ])

    # Wound repair - Simple
    codes.extend([
        {'code': '12001', 'category': 'Surgery', 'paraphrased_desc': 'Simple repair of wound, 2.5 cm or less', 'short_desc': ''},
        {'code': '12002', 'category': 'Surgery', 'paraphrased_desc': 'Simple repair of wound, 2.6-7.5 cm', 'short_desc': ''},
        {'code': '12004', 'category': 'Surgery', 'paraphrased_desc': 'Simple repair of wound, 7.6-12.5 cm', 'short_desc': ''},
        {'code': '12011', 'category': 'Surgery', 'paraphrased_desc': 'Simple repair of face/ears/eyelids/nose/lips/mucous membranes, 2.5 cm or less', 'short_desc': ''},
        {'code': '12013', 'category': 'Surgery', 'paraphrased_desc': 'Simple repair of face/ears/eyelids/nose/lips/mucous membranes, 2.6-5.0 cm', 'short_desc': ''},
    ])

    # Colonoscopy
    codes.extend([
        {'code': '45378', 'category': 'Surgery', 'paraphrased_desc': 'Diagnostic colonoscopy with examination of entire colon', 'short_desc': ''},
        {'code': '45380', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with biopsy, single or multiple', 'short_desc': ''},
        {'code': '45385', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with removal of polyp by snare technique', 'short_desc': ''},
    ])

    # Upper endoscopy (EGD)
    codes.extend([
        {'code': '43235', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy, diagnostic examination of esophagus, stomach, and duodenum', 'short_desc': ''},
        {'code': '43239', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with biopsy, single or multiple', 'short_desc': ''},
    ])

    # Cataract surgery (66984)
    codes.append({
        'code': '66984',
        'category': 'Surgery',
        'paraphrased_desc': 'Cataract removal with insertion of intraocular lens',
        'short_desc': '',
    })

    # Joint injections
    codes.extend([
        {'code': '20610', 'category': 'Surgery', 'paraphrased_desc': 'Drainage or injection into major joint or bursa', 'short_desc': ''},
        {'code': '20605', 'category': 'Surgery', 'paraphrased_desc': 'Drainage or injection into intermediate joint or bursa', 'short_desc': ''},
        {'code': '20600', 'category': 'Surgery', 'paraphrased_desc': 'Drainage or injection into small joint or bursa', 'short_desc': ''},
    ])

    # Trigger point injections (20552-20553)
    codes.extend([
        {'code': '20552', 'category': 'Surgery', 'paraphrased_desc': 'Injection of trigger point, 1-2 muscles', 'short_desc': ''},
        {'code': '20553', 'category': 'Surgery', 'paraphrased_desc': 'Injection of trigger point, 3 or more muscles', 'short_desc': ''},
    ])

    # Carpal tunnel release (64721)
    codes.append({
        'code': '64721',
        'category': 'Surgery',
        'paraphrased_desc': 'Surgical decompression of carpal tunnel',
        'short_desc': '',
    })

    # Knee arthroscopy
    codes.extend([
        {'code': '29870', 'category': 'Surgery', 'paraphrased_desc': 'Knee arthroscopy, diagnostic with or without synovial biopsy', 'short_desc': ''},
        {'code': '29881', 'category': 'Surgery', 'paraphrased_desc': 'Knee arthroscopy with meniscectomy (removal of torn cartilage)', 'short_desc': ''},
    ])

    # Shoulder arthroscopy
    codes.extend([
        {'code': '29805', 'category': 'Surgery', 'paraphrased_desc': 'Shoulder arthroscopy, diagnostic with or without synovial biopsy', 'short_desc': ''},
        {'code': '29826', 'category': 'Surgery', 'paraphrased_desc': 'Shoulder arthroscopy with decompression of subacromial space', 'short_desc': ''},
    ])

    # Tonsillectomy (42826)
    codes.append({
        'code': '42826',
        'category': 'Surgery',
        'paraphrased_desc': 'Tonsillectomy, patient age 12 or over',
        'short_desc': '',
    })

    # Appendectomy (44970)
    codes.append({
        'code': '44970',
        'category': 'Surgery',
        'paraphrased_desc': 'Laparoscopic appendectomy',
        'short_desc': '',
    })

    # Cholecystectomy (47562)
    codes.append({
        'code': '47562',
        'category': 'Surgery',
        'paraphrased_desc': 'Laparoscopic cholecystectomy (gallbladder removal)',
        'short_desc': '',
    })

    # Hernia repair
    codes.extend([
        {'code': '49505', 'category': 'Surgery', 'paraphrased_desc': 'Inguinal hernia repair, age 5 years or older', 'short_desc': ''},
        {'code': '49520', 'category': 'Surgery', 'paraphrased_desc': 'Recurrent inguinal hernia repair, any age', 'short_desc': ''},
        {'code': '49585', 'category': 'Surgery', 'paraphrased_desc': 'Umbilical hernia repair, age 5 years or older', 'short_desc': ''},
        {'code': '49650', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic inguinal hernia repair, initial', 'short_desc': ''},
        {'code': '49651', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic inguinal hernia repair, recurrent', 'short_desc': ''},
        {'code': '49652', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic ventral or incisional hernia repair', 'short_desc': ''},
        {'code': '49653', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic ventral hernia repair, incarcerated', 'short_desc': ''},
    ])

    # EXPANSION: Integumentary/Mohs surgery
    codes.extend([
        {'code': '17311', 'category': 'Surgery', 'paraphrased_desc': 'Mohs micrographic surgery, head, neck, hands, feet, first stage', 'short_desc': ''},
        {'code': '17312', 'category': 'Surgery', 'paraphrased_desc': 'Mohs micrographic surgery, head, neck, hands, feet, additional stage', 'short_desc': ''},
        {'code': '17313', 'category': 'Surgery', 'paraphrased_desc': 'Mohs micrographic surgery, trunk, arms, legs, first stage', 'short_desc': ''},
        {'code': '17314', 'category': 'Surgery', 'paraphrased_desc': 'Mohs micrographic surgery, trunk, arms, legs, additional stage', 'short_desc': ''},
        {'code': '15002', 'category': 'Surgery', 'paraphrased_desc': 'Surgical preparation of recipient site for skin graft, first 100 sq cm', 'short_desc': ''},
        {'code': '15003', 'category': 'Surgery', 'paraphrased_desc': 'Surgical preparation for skin graft, each additional 100 sq cm', 'short_desc': ''},
        {'code': '15100', 'category': 'Surgery', 'paraphrased_desc': 'Split-thickness skin graft, first 100 sq cm', 'short_desc': ''},
        {'code': '15101', 'category': 'Surgery', 'paraphrased_desc': 'Split-thickness skin graft, each additional 100 sq cm', 'short_desc': ''},
        {'code': '15120', 'category': 'Surgery', 'paraphrased_desc': 'Split-thickness skin graft, face, scalp, first 100 sq cm', 'short_desc': ''},
        {'code': '15121', 'category': 'Surgery', 'paraphrased_desc': 'Split-thickness skin graft, face, scalp, each additional 100 sq cm', 'short_desc': ''},
        {'code': '15240', 'category': 'Surgery', 'paraphrased_desc': 'Full-thickness skin graft, first 20 sq cm or less', 'short_desc': ''},
        {'code': '15241', 'category': 'Surgery', 'paraphrased_desc': 'Full-thickness skin graft, each additional 20 sq cm', 'short_desc': ''},
    ])

    # EXPANSION: Breast procedures
    codes.extend([
        {'code': '19081', 'category': 'Surgery', 'paraphrased_desc': 'Breast biopsy with placement of localization device, percutaneous, first lesion', 'short_desc': ''},
        {'code': '19082', 'category': 'Surgery', 'paraphrased_desc': 'Breast biopsy with localization, percutaneous, each additional lesion', 'short_desc': ''},
        {'code': '19083', 'category': 'Surgery', 'paraphrased_desc': 'Breast biopsy with clip placement, percutaneous, first lesion', 'short_desc': ''},
        {'code': '19084', 'category': 'Surgery', 'paraphrased_desc': 'Breast biopsy with clip placement, percutaneous, each additional lesion', 'short_desc': ''},
        {'code': '19120', 'category': 'Surgery', 'paraphrased_desc': 'Excision of breast lesion', 'short_desc': ''},
        {'code': '19125', 'category': 'Surgery', 'paraphrased_desc': 'Excision of breast lesion with preoperative placement of localization device', 'short_desc': ''},
        {'code': '19301', 'category': 'Surgery', 'paraphrased_desc': 'Partial mastectomy with axillary lymph node removal', 'short_desc': ''},
        {'code': '19302', 'category': 'Surgery', 'paraphrased_desc': 'Partial mastectomy with sentinel lymph node biopsy', 'short_desc': ''},
        {'code': '19303', 'category': 'Surgery', 'paraphrased_desc': 'Simple mastectomy', 'short_desc': ''},
        {'code': '19304', 'category': 'Surgery', 'paraphrased_desc': 'Subcutaneous mastectomy', 'short_desc': ''},
        {'code': '19305', 'category': 'Surgery', 'paraphrased_desc': 'Radical mastectomy', 'short_desc': ''},
        {'code': '19316', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with tissue expander', 'short_desc': ''},
        {'code': '19318', 'category': 'Surgery', 'paraphrased_desc': 'Breast reduction mammoplasty', 'short_desc': ''},
        {'code': '19324', 'category': 'Surgery', 'paraphrased_desc': 'Breast enlargement with breast implant', 'short_desc': ''},
        {'code': '19328', 'category': 'Surgery', 'paraphrased_desc': 'Breast implant removal', 'short_desc': ''},
        {'code': '19330', 'category': 'Surgery', 'paraphrased_desc': 'Breast implant removal with capsulectomy', 'short_desc': ''},
        {'code': '19340', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with tissue flap', 'short_desc': ''},
        {'code': '19342', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with tissue flap and implant', 'short_desc': ''},
        {'code': '19350', 'category': 'Surgery', 'paraphrased_desc': 'Nipple reconstruction', 'short_desc': ''},
        {'code': '19355', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction, free flap', 'short_desc': ''},
        {'code': '19357', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction, single stage', 'short_desc': ''},
        {'code': '19361', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with latissimus dorsi flap', 'short_desc': ''},
        {'code': '19364', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with free flap', 'short_desc': ''},
        {'code': '19366', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with other technique', 'short_desc': ''},
        {'code': '19367', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with transverse rectus abdominis myocutaneous flap', 'short_desc': ''},
        {'code': '19368', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with deep inferior epigastric perforator flap', 'short_desc': ''},
        {'code': '19369', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with superficial inferior epigastric artery flap', 'short_desc': ''},
        {'code': '19370', 'category': 'Surgery', 'paraphrased_desc': 'Breast reconstruction with gluteal artery perforator flap', 'short_desc': ''},
        {'code': '19371', 'category': 'Surgery', 'paraphrased_desc': 'Pedicle flap to breast reconstruction', 'short_desc': ''},
        {'code': '19380', 'category': 'Surgery', 'paraphrased_desc': 'Breast revision', 'short_desc': ''},
    ])

    # EXPANSION: GI procedures
    codes.extend([
        {'code': '43246', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with directed placement of feeding tube', 'short_desc': ''},
        {'code': '43247', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with removal of foreign body', 'short_desc': ''},
        {'code': '43248', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with biopsy, hot biopsy forceps', 'short_desc': ''},
        {'code': '43249', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with balloon dilation of esophagus', 'short_desc': ''},
        {'code': '43250', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with removal of tumor or polyp by snare', 'short_desc': ''},
        {'code': '43251', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with removal of tumor by hot biopsy forceps', 'short_desc': ''},
        {'code': '43252', 'category': 'Surgery', 'paraphrased_desc': 'Upper GI endoscopy with optical endomicroscopy', 'short_desc': ''},
        {'code': '43270', 'category': 'Surgery', 'paraphrased_desc': 'ERCP diagnostic', 'short_desc': ''},
        {'code': '43274', 'category': 'Surgery', 'paraphrased_desc': 'ERCP with placement of stent', 'short_desc': ''},
        {'code': '43644', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic gastric bypass', 'short_desc': ''},
        {'code': '43645', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic gastric restrictive procedure with gastric bypass', 'short_desc': ''},
        {'code': '43770', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic gastric restrictive procedure, adjustable band', 'short_desc': ''},
        {'code': '43775', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic gastric restrictive procedure, sleeve gastrectomy', 'short_desc': ''},
        {'code': '44120', 'category': 'Surgery', 'paraphrased_desc': 'Enterectomy, resection of small intestine, single', 'short_desc': ''},
        {'code': '44140', 'category': 'Surgery', 'paraphrased_desc': 'Colectomy, partial', 'short_desc': ''},
        {'code': '44160', 'category': 'Surgery', 'paraphrased_desc': 'Colectomy with removal of terminal ileum', 'short_desc': ''},
        {'code': '44204', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic colectomy, partial', 'short_desc': ''},
        {'code': '44205', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic colectomy, partial with removal of terminal ileum', 'short_desc': ''},
        {'code': '44206', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic colectomy, partial with colostomy', 'short_desc': ''},
        {'code': '44207', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic colectomy, partial with coloproctostomy', 'short_desc': ''},
        {'code': '44208', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic colectomy, partial with anastomosis', 'short_desc': ''},
        {'code': '44950', 'category': 'Surgery', 'paraphrased_desc': 'Appendectomy', 'short_desc': ''},
        {'code': '45378', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with biopsy, hot biopsy forceps', 'short_desc': ''},
        {'code': '45381', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with directed submucosal injection', 'short_desc': ''},
        {'code': '45382', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with control of bleeding', 'short_desc': ''},
        {'code': '45383', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with ablation of tumor or polyp', 'short_desc': ''},
        {'code': '45384', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with removal of tumor, polyp, or lesion by hot biopsy forceps', 'short_desc': ''},
        {'code': '45388', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with ablation of tumor by any method', 'short_desc': ''},
        {'code': '45391', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with endoscopic ultrasound examination', 'short_desc': ''},
        {'code': '45392', 'category': 'Surgery', 'paraphrased_desc': 'Colonoscopy with transendoscopic ultrasound-guided biopsy', 'short_desc': ''},
        {'code': '46020', 'category': 'Surgery', 'paraphrased_desc': 'Placement of seton for anal fistula', 'short_desc': ''},
        {'code': '46221', 'category': 'Surgery', 'paraphrased_desc': 'Hemorrhoidectomy, internal, by rubber band ligation', 'short_desc': ''},
        {'code': '46250', 'category': 'Surgery', 'paraphrased_desc': 'Hemorrhoidectomy, external, 2 or more columns/groups', 'short_desc': ''},
        {'code': '46255', 'category': 'Surgery', 'paraphrased_desc': 'Hemorrhoidectomy, internal and external, simple', 'short_desc': ''},
        {'code': '46257', 'category': 'Surgery', 'paraphrased_desc': 'Hemorrhoidectomy, internal and external, complex', 'short_desc': ''},
        {'code': '46260', 'category': 'Surgery', 'paraphrased_desc': 'Hemorrhoidectomy, internal and external, 2 or more columns/groups', 'short_desc': ''},
        {'code': '46270', 'category': 'Surgery', 'paraphrased_desc': 'Surgical treatment of anal fistula', 'short_desc': ''},
        {'code': '46275', 'category': 'Surgery', 'paraphrased_desc': 'Surgical treatment of anal fistula, complex', 'short_desc': ''},
        {'code': '46280', 'category': 'Surgery', 'paraphrased_desc': 'Surgical treatment of anal fistula with fistulectomy', 'short_desc': ''},
        {'code': '46285', 'category': 'Surgery', 'paraphrased_desc': 'Surgical treatment of anal fistula, second stage', 'short_desc': ''},
        {'code': '46320', 'category': 'Surgery', 'paraphrased_desc': 'Removal of hemorrhoids by ligation', 'short_desc': ''},
        {'code': '46600', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy, diagnostic', 'short_desc': ''},
        {'code': '46601', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy, diagnostic with sampling', 'short_desc': ''},
        {'code': '46606', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy with biopsy', 'short_desc': ''},
        {'code': '46607', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy with high-resolution magnification', 'short_desc': ''},
        {'code': '46608', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy with removal of foreign body', 'short_desc': ''},
        {'code': '46610', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy with removal of single tumor or polyp', 'short_desc': ''},
        {'code': '46611', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy with removal of multiple tumors or polyps', 'short_desc': ''},
        {'code': '46612', 'category': 'Surgery', 'paraphrased_desc': 'Anoscopy with removal of multiple tumors or polyps by hot biopsy forceps', 'short_desc': ''},
    ])

    # EXPANSION: GU procedures
    codes.extend([
        {'code': '50040', 'category': 'Surgery', 'paraphrased_desc': 'Nephrostomy, nephrotomy with drainage', 'short_desc': ''},
        {'code': '50045', 'category': 'Surgery', 'paraphrased_desc': 'Nephrotomy with exploration', 'short_desc': ''},
        {'code': '50060', 'category': 'Surgery', 'paraphrased_desc': 'Removal of kidney stone, open', 'short_desc': ''},
        {'code': '50080', 'category': 'Surgery', 'paraphrased_desc': 'Percutaneous nephrostolithotomy or pyelostolithotomy', 'short_desc': ''},
        {'code': '50543', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic partial nephrectomy', 'short_desc': ''},
        {'code': '50545', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic radical nephrectomy', 'short_desc': ''},
        {'code': '50546', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic nephrectomy including partial ureterectomy', 'short_desc': ''},
        {'code': '51702', 'category': 'Surgery', 'paraphrased_desc': 'Insertion of temporary bladder catheter', 'short_desc': ''},
        {'code': '51703', 'category': 'Surgery', 'paraphrased_desc': 'Insertion of temporary bladder catheter, complicated', 'short_desc': ''},
        {'code': '51705', 'category': 'Surgery', 'paraphrased_desc': 'Change of cystostomy tube', 'short_desc': ''},
        {'code': '51798', 'category': 'Surgery', 'paraphrased_desc': 'Measurement of post-void urine residual by ultrasound', 'short_desc': ''},
        {'code': '52000', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy', 'short_desc': ''},
        {'code': '52001', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with irrigation and evacuation', 'short_desc': ''},
        {'code': '52005', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteral catheterization', 'short_desc': ''},
        {'code': '52007', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteral catheterization with ureteroscopy', 'short_desc': ''},
        {'code': '52010', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ejaculatory duct catheterization', 'short_desc': ''},
        {'code': '52204', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with biopsy', 'short_desc': ''},
        {'code': '52214', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with fulguration of trigone', 'short_desc': ''},
        {'code': '52224', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with fulguration of minor lesion', 'short_desc': ''},
        {'code': '52234', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with fulguration of small bladder tumor', 'short_desc': ''},
        {'code': '52235', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with fulguration of medium bladder tumor', 'short_desc': ''},
        {'code': '52240', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with fulguration of large bladder tumor', 'short_desc': ''},
        {'code': '52250', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with insertion of radioactive substance', 'short_desc': ''},
        {'code': '52260', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with dilation of bladder neck', 'short_desc': ''},
        {'code': '52276', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with direct vision urethrotomy', 'short_desc': ''},
        {'code': '52281', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with calibration and dilation of urethra', 'short_desc': ''},
        {'code': '52282', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with injection for cystography', 'short_desc': ''},
        {'code': '52283', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with steroid injection', 'short_desc': ''},
        {'code': '52287', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with injection for treatment of urinary incontinence', 'short_desc': ''},
        {'code': '52310', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with removal of foreign body or calculus', 'short_desc': ''},
        {'code': '52315', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with removal of bladder calculus', 'short_desc': ''},
        {'code': '52320', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with removal of ureteral calculus', 'short_desc': ''},
        {'code': '52325', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with fragmentation of ureteral calculus', 'short_desc': ''},
        {'code': '52330', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with manipulation of ureteral calculus', 'short_desc': ''},
        {'code': '52332', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with insertion of ureteral stent', 'short_desc': ''},
        {'code': '52334', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with insertion of ureteral guide wire', 'short_desc': ''},
        {'code': '52341', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with treatment of ureteral stricture', 'short_desc': ''},
        {'code': '52342', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with treatment of ureteropelvic junction stricture', 'short_desc': ''},
        {'code': '52343', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with treatment of intra-renal stricture', 'short_desc': ''},
        {'code': '52344', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy', 'short_desc': ''},
        {'code': '52345', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy and treatment of ureter stone', 'short_desc': ''},
        {'code': '52346', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy and treatment of kidney stone', 'short_desc': ''},
        {'code': '52351', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy and biopsy', 'short_desc': ''},
        {'code': '52352', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy and removal or manipulation of calculus', 'short_desc': ''},
        {'code': '52353', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy and lithotripsy', 'short_desc': ''},
        {'code': '52354', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy and treatment of ureteral lesion', 'short_desc': ''},
        {'code': '52355', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with ureteroscopy and excision of ureteral tumor', 'short_desc': ''},
        {'code': '52400', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with incision of bladder neck', 'short_desc': ''},
        {'code': '52402', 'category': 'Surgery', 'paraphrased_desc': 'Cystourethroscopy with transurethral resection', 'short_desc': ''},
        {'code': '52500', 'category': 'Surgery', 'paraphrased_desc': 'Transurethral resection of bladder neck', 'short_desc': ''},
        {'code': '52601', 'category': 'Surgery', 'paraphrased_desc': 'Transurethral resection of prostate (TURP), complete', 'short_desc': ''},
        {'code': '52630', 'category': 'Surgery', 'paraphrased_desc': 'Transurethral resection of prostate (TURP), residual or regrowth', 'short_desc': ''},
        {'code': '52647', 'category': 'Surgery', 'paraphrased_desc': 'Laser vaporization of prostate', 'short_desc': ''},
        {'code': '52648', 'category': 'Surgery', 'paraphrased_desc': 'Laser vaporization of prostate, including control of postoperative bleeding', 'short_desc': ''},
        {'code': '52649', 'category': 'Surgery', 'paraphrased_desc': 'Laser enucleation of prostate', 'short_desc': ''},
        {'code': '54150', 'category': 'Surgery', 'paraphrased_desc': 'Circumcision using clamp or device', 'short_desc': ''},
        {'code': '54160', 'category': 'Surgery', 'paraphrased_desc': 'Circumcision, surgical excision other than clamp', 'short_desc': ''},
        {'code': '54161', 'category': 'Surgery', 'paraphrased_desc': 'Circumcision, surgical excision, newborn', 'short_desc': ''},
        {'code': '54162', 'category': 'Surgery', 'paraphrased_desc': 'Lysis or excision of penile adhesions, newborn', 'short_desc': ''},
        {'code': '54163', 'category': 'Surgery', 'paraphrased_desc': 'Repair of incomplete circumcision', 'short_desc': ''},
        {'code': '55250', 'category': 'Surgery', 'paraphrased_desc': 'Vasectomy', 'short_desc': ''},
        {'code': '55400', 'category': 'Surgery', 'paraphrased_desc': 'Vasotomy for vasograms, reversal procedures', 'short_desc': ''},
        {'code': '55550', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic repair of inguinal hernia', 'short_desc': ''},
        {'code': '55700', 'category': 'Surgery', 'paraphrased_desc': 'Biopsy of prostate, needle or punch, single or multiple', 'short_desc': ''},
        {'code': '56605', 'category': 'Surgery', 'paraphrased_desc': 'Vulvectomy, simple, partial', 'short_desc': ''},
        {'code': '56620', 'category': 'Surgery', 'paraphrased_desc': 'Vulvectomy, simple, complete', 'short_desc': ''},
        {'code': '56630', 'category': 'Surgery', 'paraphrased_desc': 'Vulvectomy, radical, partial', 'short_desc': ''},
        {'code': '56633', 'category': 'Surgery', 'paraphrased_desc': 'Vulvectomy, radical, complete', 'short_desc': ''},
        {'code': '56637', 'category': 'Surgery', 'paraphrased_desc': 'Vulvectomy, radical, complete with inguinofemoral lymphadenectomy', 'short_desc': ''},
        {'code': '56640', 'category': 'Surgery', 'paraphrased_desc': 'Vulvectomy, radical, complete with bilateral inguinofemoral lymphadenectomy', 'short_desc': ''},
        {'code': '57100', 'category': 'Surgery', 'paraphrased_desc': 'Biopsy of vagina, simple', 'short_desc': ''},
        {'code': '57105', 'category': 'Surgery', 'paraphrased_desc': 'Biopsy of vagina, extensive', 'short_desc': ''},
        {'code': '57106', 'category': 'Surgery', 'paraphrased_desc': 'Vaginectomy, partial', 'short_desc': ''},
        {'code': '57107', 'category': 'Surgery', 'paraphrased_desc': 'Vaginectomy, partial with removal of vaginal wall', 'short_desc': ''},
        {'code': '57110', 'category': 'Surgery', 'paraphrased_desc': 'Vaginectomy, complete', 'short_desc': ''},
        {'code': '57111', 'category': 'Surgery', 'paraphrased_desc': 'Vaginectomy, complete with removal of vaginal wall', 'short_desc': ''},
        {'code': '57112', 'category': 'Surgery', 'paraphrased_desc': 'Vaginectomy, complete with removal of vaginal wall with pelvic floor repair', 'short_desc': ''},
        {'code': '57240', 'category': 'Surgery', 'paraphrased_desc': 'Anterior colporrhaphy for cystocele repair', 'short_desc': ''},
        {'code': '57250', 'category': 'Surgery', 'paraphrased_desc': 'Posterior colporrhaphy for rectocele repair', 'short_desc': ''},
        {'code': '57260', 'category': 'Surgery', 'paraphrased_desc': 'Combined anterior and posterior colporrhaphy', 'short_desc': ''},
        {'code': '57265', 'category': 'Surgery', 'paraphrased_desc': 'Combined anterior and posterior colporrhaphy with enterocele repair', 'short_desc': ''},
        {'code': '57268', 'category': 'Surgery', 'paraphrased_desc': 'Repair of enterocele', 'short_desc': ''},
        {'code': '57270', 'category': 'Surgery', 'paraphrased_desc': 'Repair of enterocele with colpectomy', 'short_desc': ''},
        {'code': '57280', 'category': 'Surgery', 'paraphrased_desc': 'Colpopexy, abdominal approach', 'short_desc': ''},
        {'code': '57282', 'category': 'Surgery', 'paraphrased_desc': 'Colpopexy, vaginal approach, extra-peritoneal', 'short_desc': ''},
        {'code': '57283', 'category': 'Surgery', 'paraphrased_desc': 'Colpopexy, vaginal approach, intra-peritoneal', 'short_desc': ''},
        {'code': '57284', 'category': 'Surgery', 'paraphrased_desc': 'Paravaginal defect repair', 'short_desc': ''},
        {'code': '57288', 'category': 'Surgery', 'paraphrased_desc': 'Sling operation for stress incontinence', 'short_desc': ''},
        {'code': '57289', 'category': 'Surgery', 'paraphrased_desc': 'Pereyra procedure', 'short_desc': ''},
        {'code': '57452', 'category': 'Surgery', 'paraphrased_desc': 'Colposcopy of cervix', 'short_desc': ''},
        {'code': '57454', 'category': 'Surgery', 'paraphrased_desc': 'Colposcopy of cervix with biopsy', 'short_desc': ''},
        {'code': '57455', 'category': 'Surgery', 'paraphrased_desc': 'Colposcopy of cervix with biopsy and endocervical curettage', 'short_desc': ''},
        {'code': '57456', 'category': 'Surgery', 'paraphrased_desc': 'Colposcopy of cervix with endocervical curettage', 'short_desc': ''},
        {'code': '57460', 'category': 'Surgery', 'paraphrased_desc': 'Colposcopy of cervix with loop electrode excision', 'short_desc': ''},
        {'code': '57461', 'category': 'Surgery', 'paraphrased_desc': 'Colposcopy of cervix with loop electrode conization', 'short_desc': ''},
        {'code': '57500', 'category': 'Surgery', 'paraphrased_desc': 'Biopsy of cervix, single or multiple', 'short_desc': ''},
        {'code': '57505', 'category': 'Surgery', 'paraphrased_desc': 'Endocervical curettage', 'short_desc': ''},
        {'code': '57510', 'category': 'Surgery', 'paraphrased_desc': 'Cautery of cervix, electro or thermal', 'short_desc': ''},
        {'code': '57511', 'category': 'Surgery', 'paraphrased_desc': 'Cryotherapy of cervix', 'short_desc': ''},
        {'code': '57513', 'category': 'Surgery', 'paraphrased_desc': 'Laser surgery of cervix', 'short_desc': ''},
        {'code': '57520', 'category': 'Surgery', 'paraphrased_desc': 'Conization of cervix with or without fulguration', 'short_desc': ''},
        {'code': '57522', 'category': 'Surgery', 'paraphrased_desc': 'Conization of cervix with or without fulguration, with dilation and curettage', 'short_desc': ''},
        {'code': '57530', 'category': 'Surgery', 'paraphrased_desc': 'Trachelectomy, amputation of cervix', 'short_desc': ''},
        {'code': '58100', 'category': 'Surgery', 'paraphrased_desc': 'Endometrial biopsy', 'short_desc': ''},
        {'code': '58120', 'category': 'Surgery', 'paraphrased_desc': 'Dilation and curettage, diagnostic', 'short_desc': ''},
        {'code': '58140', 'category': 'Surgery', 'paraphrased_desc': 'Myomectomy, removal of fibroid tumor, single', 'short_desc': ''},
        {'code': '58145', 'category': 'Surgery', 'paraphrased_desc': 'Myomectomy, removal of fibroid tumor, multiple', 'short_desc': ''},
        {'code': '58146', 'category': 'Surgery', 'paraphrased_desc': 'Myomectomy, removal of fibroid tumor, myomectomy with total hysterectomy', 'short_desc': ''},
        {'code': '58150', 'category': 'Surgery', 'paraphrased_desc': 'Total hysterectomy', 'short_desc': ''},
        {'code': '58152', 'category': 'Surgery', 'paraphrased_desc': 'Total hysterectomy with removal of tube(s) and ovary(s)', 'short_desc': ''},
        {'code': '58180', 'category': 'Surgery', 'paraphrased_desc': 'Supracervical hysterectomy', 'short_desc': ''},
        {'code': '58260', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy', 'short_desc': ''},
        {'code': '58262', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy with removal of tube(s) and/or ovary(s)', 'short_desc': ''},
        {'code': '58263', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy with removal of tube(s), ovary(s), and repair of enterocele', 'short_desc': ''},
        {'code': '58267', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy with colpo-urethrocystopexy', 'short_desc': ''},
        {'code': '58270', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy with repair of enterocele', 'short_desc': ''},
        {'code': '58275', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy with total or partial vaginectomy', 'short_desc': ''},
        {'code': '58280', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy with repair of enterocele and repair of vaginal vault prolapse', 'short_desc': ''},
        {'code': '58290', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy, complex', 'short_desc': ''},
        {'code': '58291', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy, complex with removal of tube(s) and/or ovary(s)', 'short_desc': ''},
        {'code': '58292', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy, complex with removal of tube(s), ovary(s), and repair of enterocele', 'short_desc': ''},
        {'code': '58293', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy, complex with colpo-urethrocystopexy', 'short_desc': ''},
        {'code': '58294', 'category': 'Surgery', 'paraphrased_desc': 'Vaginal hysterectomy, complex with repair of enterocele', 'short_desc': ''},
        {'code': '58541', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic hysterectomy', 'short_desc': ''},
        {'code': '58542', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic hysterectomy with removal of tube(s) and/or ovary(s)', 'short_desc': ''},
        {'code': '58543', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic hysterectomy, supracervical', 'short_desc': ''},
        {'code': '58544', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic hysterectomy with removal of tube(s) and/or ovary(s), supracervical', 'short_desc': ''},
        {'code': '58545', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic hysterectomy, total or radical', 'short_desc': ''},
        {'code': '58546', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic hysterectomy with removal of tube(s) and/or ovary(s), total or radical', 'short_desc': ''},
        {'code': '58548', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopic radical hysterectomy with pelvic lymphadenectomy', 'short_desc': ''},
        {'code': '58550', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopy, surgical, with vaginal hysterectomy', 'short_desc': ''},
        {'code': '58552', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopy, surgical, with vaginal hysterectomy and removal of tube(s) and/or ovary(s)', 'short_desc': ''},
        {'code': '58553', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopy, surgical, with vaginal hysterectomy and total or partial vaginectomy', 'short_desc': ''},
        {'code': '58554', 'category': 'Surgery', 'paraphrased_desc': 'Laparoscopy, surgical, with vaginal hysterectomy and repair of enterocele', 'short_desc': ''},
    ])

    # EXPANSION: Orthopedic procedures
    codes.extend([
        {'code': '23350', 'category': 'Surgery', 'paraphrased_desc': 'Injection procedure for shoulder arthrography', 'short_desc': ''},
        {'code': '23470', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of shoulder joint, hemiarthroplasty', 'short_desc': ''},
        {'code': '23472', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of shoulder joint, total shoulder replacement', 'short_desc': ''},
        {'code': '23473', 'category': 'Surgery', 'paraphrased_desc': 'Revision of total shoulder arthroplasty', 'short_desc': ''},
        {'code': '23474', 'category': 'Surgery', 'paraphrased_desc': 'Revision of total shoulder replacement with glenoid and humeral component', 'short_desc': ''},
        {'code': '24360', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of elbow joint', 'short_desc': ''},
        {'code': '24361', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of elbow joint with distal humerus and proximal ulna replacement', 'short_desc': ''},
        {'code': '24362', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of elbow joint with implant and fascia lata autograft', 'short_desc': ''},
        {'code': '24363', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of elbow joint, revision of total elbow arthroplasty', 'short_desc': ''},
        {'code': '25441', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty with prosthetic replacement, distal radius', 'short_desc': ''},
        {'code': '25442', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty with prosthetic replacement, distal ulna', 'short_desc': ''},
        {'code': '25443', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty with prosthetic replacement, distal radius and ulna', 'short_desc': ''},
        {'code': '25444', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty with prosthetic replacement, scaphoid carpal bone', 'short_desc': ''},
        {'code': '25445', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty with prosthetic replacement, lunate carpal bone', 'short_desc': ''},
        {'code': '25446', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty with prosthetic replacement, trapezium carpal bone', 'short_desc': ''},
        {'code': '25447', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty with prosthetic replacement, distal radius and partial or complete carpus', 'short_desc': ''},
        {'code': '27130', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of hip, partial hip replacement', 'short_desc': ''},
        {'code': '27132', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of hip, femoral component only with bone graft', 'short_desc': ''},
        {'code': '27134', 'category': 'Surgery', 'paraphrased_desc': 'Revision of total hip arthroplasty, acetabular component only', 'short_desc': ''},
        {'code': '27137', 'category': 'Surgery', 'paraphrased_desc': 'Revision of total hip arthroplasty, femoral and acetabular components', 'short_desc': ''},
        {'code': '27138', 'category': 'Surgery', 'paraphrased_desc': 'Revision of total hip arthroplasty, femoral component only', 'short_desc': ''},
        {'code': '27446', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of knee, condyle and plateau, medial or lateral compartment', 'short_desc': ''},
        {'code': '27447', 'category': 'Surgery', 'paraphrased_desc': 'Arthroplasty of knee, condyle and plateau, medial and lateral compartment', 'short_desc': ''},
        {'code': '27486', 'category': 'Surgery', 'paraphrased_desc': 'Revision of total knee arthroplasty, femoral component', 'short_desc': ''},
        {'code': '27487', 'category': 'Surgery', 'paraphrased_desc': 'Revision of total knee arthroplasty, tibial component', 'short_desc': ''},
        {'code': '27488', 'category': 'Surgery', 'paraphrased_desc': 'Removal of prosthesis, knee joint', 'short_desc': ''},
        {'code': '28285', 'category': 'Surgery', 'paraphrased_desc': 'Hammertoe correction with tendon transfer', 'short_desc': ''},
        {'code': '28290', 'category': 'Surgery', 'paraphrased_desc': 'Hammertoe correction with simple tenotomy', 'short_desc': ''},
        {'code': '28292', 'category': 'Surgery', 'paraphrased_desc': 'Hammertoe correction with joint resection', 'short_desc': ''},
        {'code': '28293', 'category': 'Surgery', 'paraphrased_desc': 'Hammertoe correction with open or percutaneous arthroplasty', 'short_desc': ''},
        {'code': '28294', 'category': 'Surgery', 'paraphrased_desc': 'Hammertoe correction with open or percutaneous arthroplasty, each additional toe', 'short_desc': ''},
        {'code': '28296', 'category': 'Surgery', 'paraphrased_desc': 'Bunionectomy with simple exostectomy', 'short_desc': ''},
        {'code': '28297', 'category': 'Surgery', 'paraphrased_desc': 'Bunionectomy with exostectomy and soft tissue correction', 'short_desc': ''},
        {'code': '28298', 'category': 'Surgery', 'paraphrased_desc': 'Bunionectomy with distal metatarsal osteotomy', 'short_desc': ''},
        {'code': '28299', 'category': 'Surgery', 'paraphrased_desc': 'Bunionectomy with proximal metatarsal osteotomy', 'short_desc': ''},
        {'code': '29826', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy shoulder, surgical, decompression of subacromial space', 'short_desc': ''},
        {'code': '29827', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy shoulder, surgical, with rotator cuff repair', 'short_desc': ''},
        {'code': '29880', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, with meniscectomy', 'short_desc': ''},
        {'code': '29882', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, with meniscus repair', 'short_desc': ''},
        {'code': '29883', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, with meniscus repair and synovectomy', 'short_desc': ''},
        {'code': '29884', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, with lysis of adhesions', 'short_desc': ''},
        {'code': '29885', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, drilling for intact osteochondritis dissecans lesion', 'short_desc': ''},
        {'code': '29886', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, drilling for osteochondritis dissecans with bone grafting', 'short_desc': ''},
        {'code': '29887', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, drilling for osteochondritis dissecans with internal fixation', 'short_desc': ''},
        {'code': '29888', 'category': 'Surgery', 'paraphrased_desc': 'Arthroscopy knee, surgical, with loose body removal', 'short_desc': ''},
    ])

    # EXPANSION: ENT procedures
    codes.extend([
        {'code': '30100', 'category': 'Surgery', 'paraphrased_desc': 'Intranasal biopsy', 'short_desc': ''},
        {'code': '30110', 'category': 'Surgery', 'paraphrased_desc': 'Excision of nasal polyp, simple', 'short_desc': ''},
        {'code': '30115', 'category': 'Surgery', 'paraphrased_desc': 'Excision of nasal polyp, extensive', 'short_desc': ''},
        {'code': '30117', 'category': 'Surgery', 'paraphrased_desc': 'Excision or destruction of intranasal lesion', 'short_desc': ''},
        {'code': '30118', 'category': 'Surgery', 'paraphrased_desc': 'Excision or destruction of intranasal lesion, extensive', 'short_desc': ''},
        {'code': '30124', 'category': 'Surgery', 'paraphrased_desc': 'Excision of dermoid cyst, nose, simple', 'short_desc': ''},
        {'code': '30125', 'category': 'Surgery', 'paraphrased_desc': 'Excision of dermoid cyst, nose, complex', 'short_desc': ''},
        {'code': '30130', 'category': 'Surgery', 'paraphrased_desc': 'Excision of turbinate bones, partial or complete', 'short_desc': ''},
        {'code': '30140', 'category': 'Surgery', 'paraphrased_desc': 'Submucous resection of turbinate', 'short_desc': ''},
        {'code': '30400', 'category': 'Surgery', 'paraphrased_desc': 'Rhinoplasty, primary, lateral and alar cartilages', 'short_desc': ''},
        {'code': '30410', 'category': 'Surgery', 'paraphrased_desc': 'Rhinoplasty, primary, complete', 'short_desc': ''},
        {'code': '30420', 'category': 'Surgery', 'paraphrased_desc': 'Rhinoplasty, secondary, minor revision', 'short_desc': ''},
        {'code': '30430', 'category': 'Surgery', 'paraphrased_desc': 'Rhinoplasty, secondary, major revision', 'short_desc': ''},
        {'code': '30435', 'category': 'Surgery', 'paraphrased_desc': 'Rhinoplasty, secondary, major revision including nasal tip', 'short_desc': ''},
        {'code': '30450', 'category': 'Surgery', 'paraphrased_desc': 'Rhinoplasty, major reconstruction', 'short_desc': ''},
        {'code': '30460', 'category': 'Surgery', 'paraphrased_desc': 'Rhinoplasty, augmentation', 'short_desc': ''},
        {'code': '30520', 'category': 'Surgery', 'paraphrased_desc': 'Septoplasty for nasal airway obstruction', 'short_desc': ''},
        {'code': '30540', 'category': 'Surgery', 'paraphrased_desc': 'Repair of nasal septal perforation', 'short_desc': ''},
        {'code': '30545', 'category': 'Surgery', 'paraphrased_desc': 'Repair of nasal septal perforation, complex', 'short_desc': ''},
        {'code': '30801', 'category': 'Surgery', 'paraphrased_desc': 'Ablation of inferior turbinates, intramural, unilateral', 'short_desc': ''},
        {'code': '30802', 'category': 'Surgery', 'paraphrased_desc': 'Ablation of inferior turbinates, intramural, bilateral', 'short_desc': ''},
        {'code': '31231', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, diagnostic', 'short_desc': ''},
        {'code': '31233', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, diagnostic with maxillary sinusoscopy', 'short_desc': ''},
        {'code': '31235', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, diagnostic with sphenoid sinusoscopy', 'short_desc': ''},
        {'code': '31237', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with biopsy', 'short_desc': ''},
        {'code': '31238', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with control of nasal hemorrhage', 'short_desc': ''},
        {'code': '31240', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with concha bullosa resection', 'short_desc': ''},
        {'code': '31241', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with ligation of sphenopalatine artery', 'short_desc': ''},
        {'code': '31253', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with ethmoidectomy, partial', 'short_desc': ''},
        {'code': '31254', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with ethmoidectomy, total', 'short_desc': ''},
        {'code': '31255', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with ethmoidectomy, total and removal of tissue from sphenoid sinus', 'short_desc': ''},
        {'code': '31256', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with maxillary antrostomy', 'short_desc': ''},
        {'code': '31267', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with maxillary antrostomy and removal of tissue', 'short_desc': ''},
        {'code': '31276', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with frontal sinus exploration', 'short_desc': ''},
        {'code': '31287', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with sphenoidotomy', 'short_desc': ''},
        {'code': '31288', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with sphenoidotomy and removal of tissue', 'short_desc': ''},
        {'code': '31290', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with repair of cerebrospinal fluid leak', 'short_desc': ''},
        {'code': '31291', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with repair of cerebrospinal fluid leak and graft', 'short_desc': ''},
        {'code': '31292', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with medial or inferior orbital wall decompression', 'short_desc': ''},
        {'code': '31293', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with medial orbital wall and inferior orbital wall decompression', 'short_desc': ''},
        {'code': '31294', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with optic nerve decompression', 'short_desc': ''},
        {'code': '31295', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with dilation of maxillary sinus ostium', 'short_desc': ''},
        {'code': '31296', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with dilation of frontal and sphenoid sinus ostia', 'short_desc': ''},
        {'code': '31297', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with dilation of frontal, maxillary, and sphenoid sinus ostia', 'short_desc': ''},
        {'code': '31298', 'category': 'Surgery', 'paraphrased_desc': 'Nasal endoscopy, surgical with dilation of frontal sinus ostium', 'short_desc': ''},
        {'code': '69200', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from external auditory canal', 'short_desc': ''},
        {'code': '69205', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from external auditory canal with general anesthesia', 'short_desc': ''},
        {'code': '69210', 'category': 'Surgery', 'paraphrased_desc': 'Removal of impacted earwax, unilateral', 'short_desc': ''},
        {'code': '69222', 'category': 'Surgery', 'paraphrased_desc': 'Debridement of mastoid cavity, simple', 'short_desc': ''},
        {'code': '69420', 'category': 'Surgery', 'paraphrased_desc': 'Myringotomy', 'short_desc': ''},
        {'code': '69421', 'category': 'Surgery', 'paraphrased_desc': 'Myringotomy with aspiration', 'short_desc': ''},
        {'code': '69424', 'category': 'Surgery', 'paraphrased_desc': 'Ventilating tube removal requiring general anesthesia', 'short_desc': ''},
        {'code': '69433', 'category': 'Surgery', 'paraphrased_desc': 'Tympanostomy with local or topical anesthesia', 'short_desc': ''},
        {'code': '69436', 'category': 'Surgery', 'paraphrased_desc': 'Tympanostomy with general anesthesia', 'short_desc': ''},
        {'code': '69501', 'category': 'Surgery', 'paraphrased_desc': 'Transmastoid antrotomy', 'short_desc': ''},
        {'code': '69502', 'category': 'Surgery', 'paraphrased_desc': 'Mastoidectomy, complete', 'short_desc': ''},
        {'code': '69505', 'category': 'Surgery', 'paraphrased_desc': 'Mastoidectomy, modified radical', 'short_desc': ''},
        {'code': '69511', 'category': 'Surgery', 'paraphrased_desc': 'Mastoidectomy, radical', 'short_desc': ''},
        {'code': '69601', 'category': 'Surgery', 'paraphrased_desc': 'Revision mastoidectomy', 'short_desc': ''},
        {'code': '69602', 'category': 'Surgery', 'paraphrased_desc': 'Revision mastoidectomy with apicectomy', 'short_desc': ''},
        {'code': '69603', 'category': 'Surgery', 'paraphrased_desc': 'Revision mastoidectomy with tympanoplasty', 'short_desc': ''},
        {'code': '69604', 'category': 'Surgery', 'paraphrased_desc': 'Revision mastoidectomy with ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69605', 'category': 'Surgery', 'paraphrased_desc': 'Revision mastoidectomy with apicectomy with tympanoplasty', 'short_desc': ''},
        {'code': '69610', 'category': 'Surgery', 'paraphrased_desc': 'Tympanic membrane repair', 'short_desc': ''},
        {'code': '69620', 'category': 'Surgery', 'paraphrased_desc': 'Myringoplasty', 'short_desc': ''},
        {'code': '69631', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty without mastoidectomy, without ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69632', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty without mastoidectomy, with ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69633', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty without mastoidectomy, with ossicular chain reconstruction and synthetic prosthesis', 'short_desc': ''},
        {'code': '69635', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty without mastoidectomy, radical or complete, with ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69636', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty without mastoidectomy, radical or complete, with ossicular chain reconstruction and synthetic prosthesis', 'short_desc': ''},
        {'code': '69641', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty with mastoidectomy, without ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69642', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty with mastoidectomy, with ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69643', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty with mastoidectomy, with ossicular chain reconstruction and synthetic prosthesis', 'short_desc': ''},
        {'code': '69644', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty with mastoidectomy, with intact or reconstructed wall, without ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69645', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty with mastoidectomy, with intact or reconstructed wall, with ossicular chain reconstruction', 'short_desc': ''},
        {'code': '69646', 'category': 'Surgery', 'paraphrased_desc': 'Tympanoplasty with mastoidectomy, with intact or reconstructed wall, with ossicular chain reconstruction and synthetic prosthesis', 'short_desc': ''},
        {'code': '69650', 'category': 'Surgery', 'paraphrased_desc': 'Stapes mobilization', 'short_desc': ''},
        {'code': '69660', 'category': 'Surgery', 'paraphrased_desc': 'Stapedectomy or stapedotomy', 'short_desc': ''},
        {'code': '69661', 'category': 'Surgery', 'paraphrased_desc': 'Stapedectomy or stapedotomy with footplate drill out', 'short_desc': ''},
        {'code': '69662', 'category': 'Surgery', 'paraphrased_desc': 'Revision or removal of stapes prosthesis', 'short_desc': ''},
        {'code': '69666', 'category': 'Surgery', 'paraphrased_desc': 'Repair of oval window fistula', 'short_desc': ''},
        {'code': '69667', 'category': 'Surgery', 'paraphrased_desc': 'Repair of round window fistula', 'short_desc': ''},
        {'code': '69670', 'category': 'Surgery', 'paraphrased_desc': 'Mastoid obliteration', 'short_desc': ''},
        {'code': '69676', 'category': 'Surgery', 'paraphrased_desc': 'Tympanic neurectomy', 'short_desc': ''},
        {'code': '69711', 'category': 'Surgery', 'paraphrased_desc': 'Removal or repair of electromagnetic bone conduction hearing device', 'short_desc': ''},
        {'code': '69714', 'category': 'Surgery', 'paraphrased_desc': 'Implantation of osseointegrated implant for bone conduction', 'short_desc': ''},
        {'code': '69715', 'category': 'Surgery', 'paraphrased_desc': 'Implantation of osseointegrated implant for bone conduction, temporal bone', 'short_desc': ''},
        {'code': '69717', 'category': 'Surgery', 'paraphrased_desc': 'Replacement of osseointegrated implant for bone conduction', 'short_desc': ''},
        {'code': '69718', 'category': 'Surgery', 'paraphrased_desc': 'Replacement of osseointegrated implant for bone conduction, temporal bone', 'short_desc': ''},
        {'code': '69720', 'category': 'Surgery', 'paraphrased_desc': 'Decompression of facial nerve', 'short_desc': ''},
        {'code': '69725', 'category': 'Surgery', 'paraphrased_desc': 'Decompression of facial nerve, complete', 'short_desc': ''},
        {'code': '69740', 'category': 'Surgery', 'paraphrased_desc': 'Suture of facial nerve', 'short_desc': ''},
        {'code': '69745', 'category': 'Surgery', 'paraphrased_desc': 'Suture of facial nerve, with or without graft', 'short_desc': ''},
        {'code': '69799', 'category': 'Surgery', 'paraphrased_desc': 'Unlisted procedure, middle ear', 'short_desc': ''},
    ])

    # EXPANSION: Ophthalmology procedures
    codes.extend([
        {'code': '65091', 'category': 'Surgery', 'paraphrased_desc': 'Evisceration of eye contents', 'short_desc': ''},
        {'code': '65093', 'category': 'Surgery', 'paraphrased_desc': 'Evisceration of eye contents with implant', 'short_desc': ''},
        {'code': '65101', 'category': 'Surgery', 'paraphrased_desc': 'Enucleation of eye with or without implant', 'short_desc': ''},
        {'code': '65103', 'category': 'Surgery', 'paraphrased_desc': 'Enucleation of eye with implant and muscles attached', 'short_desc': ''},
        {'code': '65105', 'category': 'Surgery', 'paraphrased_desc': 'Enucleation of eye with implant and muscles not attached', 'short_desc': ''},
        {'code': '65110', 'category': 'Surgery', 'paraphrased_desc': 'Exenteration of orbit', 'short_desc': ''},
        {'code': '65112', 'category': 'Surgery', 'paraphrased_desc': 'Exenteration of orbit with removal of adjacent structures', 'short_desc': ''},
        {'code': '65114', 'category': 'Surgery', 'paraphrased_desc': 'Exenteration of orbit with removal of adjacent structures and bone removal', 'short_desc': ''},
        {'code': '65125', 'category': 'Surgery', 'paraphrased_desc': 'Modification of ocular implant', 'short_desc': ''},
        {'code': '65130', 'category': 'Surgery', 'paraphrased_desc': 'Insertion of ocular implant', 'short_desc': ''},
        {'code': '65135', 'category': 'Surgery', 'paraphrased_desc': 'Insertion of ocular implant following evisceration', 'short_desc': ''},
        {'code': '65140', 'category': 'Surgery', 'paraphrased_desc': 'Insertion of ocular implant following enucleation', 'short_desc': ''},
        {'code': '65150', 'category': 'Surgery', 'paraphrased_desc': 'Reinsertion of ocular implant', 'short_desc': ''},
        {'code': '65155', 'category': 'Surgery', 'paraphrased_desc': 'Reinsertion of ocular implant with or without conjunctival graft', 'short_desc': ''},
        {'code': '65175', 'category': 'Surgery', 'paraphrased_desc': 'Removal of ocular implant', 'short_desc': ''},
        {'code': '65205', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from external eye', 'short_desc': ''},
        {'code': '65210', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from external eye with slit lamp', 'short_desc': ''},
        {'code': '65220', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from external eye with general anesthesia', 'short_desc': ''},
        {'code': '65222', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from external eye with general anesthesia and incision', 'short_desc': ''},
        {'code': '65235', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from intraocular, anterior segment', 'short_desc': ''},
        {'code': '65260', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from intraocular, posterior segment, magnetic extraction', 'short_desc': ''},
        {'code': '65265', 'category': 'Surgery', 'paraphrased_desc': 'Removal of foreign body from intraocular, posterior segment, nonmagnetic extraction', 'short_desc': ''},
        {'code': '65270', 'category': 'Surgery', 'paraphrased_desc': 'Repair of laceration of conjunctiva', 'short_desc': ''},
        {'code': '65272', 'category': 'Surgery', 'paraphrased_desc': 'Repair of laceration of conjunctiva with hospitalization', 'short_desc': ''},
        {'code': '65273', 'category': 'Surgery', 'paraphrased_desc': 'Repair of laceration of conjunctiva with graft', 'short_desc': ''},
        {'code': '65275', 'category': 'Surgery', 'paraphrased_desc': 'Repair of laceration of cornea', 'short_desc': ''},
        {'code': '65280', 'category': 'Surgery', 'paraphrased_desc': 'Repair of laceration of cornea with tissue glue', 'short_desc': ''},
        {'code': '65285', 'category': 'Surgery', 'paraphrased_desc': 'Repair of laceration of cornea with graft', 'short_desc': ''},
        {'code': '65286', 'category': 'Surgery', 'paraphrased_desc': 'Repair of laceration of cornea or sclera, perforating', 'short_desc': ''},
        {'code': '66820', 'category': 'Surgery', 'paraphrased_desc': 'Discission of secondary membranous cataract', 'short_desc': ''},
        {'code': '66821', 'category': 'Surgery', 'paraphrased_desc': 'Discission of secondary membranous cataract with laser surgery', 'short_desc': ''},
        {'code': '66830', 'category': 'Surgery', 'paraphrased_desc': 'Removal of secondary membranous cataract', 'short_desc': ''},
        {'code': '66840', 'category': 'Surgery', 'paraphrased_desc': 'Removal of lens material, aspiration technique, 1 or more stages', 'short_desc': ''},
        {'code': '66850', 'category': 'Surgery', 'paraphrased_desc': 'Removal of lens material, phacofragmentation technique', 'short_desc': ''},
        {'code': '66852', 'category': 'Surgery', 'paraphrased_desc': 'Removal of lens material, pars plana approach', 'short_desc': ''},
        {'code': '66920', 'category': 'Surgery', 'paraphrased_desc': 'Removal of lens material, intracapsular', 'short_desc': ''},
        {'code': '66930', 'category': 'Surgery', 'paraphrased_desc': 'Removal of lens material, intracapsular, for dislocated lens', 'short_desc': ''},
        {'code': '66940', 'category': 'Surgery', 'paraphrased_desc': 'Removal of lens material, extracapsular', 'short_desc': ''},
        {'code': '66982', 'category': 'Surgery', 'paraphrased_desc': 'Cataract surgery, complex', 'short_desc': ''},
        {'code': '66983', 'category': 'Surgery', 'paraphrased_desc': 'Cataract surgery with intraocular lens implant, 1 stage', 'short_desc': ''},
        {'code': '66985', 'category': 'Surgery', 'paraphrased_desc': 'Insertion of intraocular lens prosthesis, secondary implant', 'short_desc': ''},
        {'code': '66986', 'category': 'Surgery', 'paraphrased_desc': 'Exchange of intraocular lens', 'short_desc': ''},
        {'code': '67005', 'category': 'Surgery', 'paraphrased_desc': 'Removal of vitreous by anterior approach', 'short_desc': ''},
        {'code': '67010', 'category': 'Surgery', 'paraphrased_desc': 'Removal of vitreous by paracentesis of anterior chamber', 'short_desc': ''},
        {'code': '67015', 'category': 'Surgery', 'paraphrased_desc': 'Aspiration or release of vitreous, subretinal or choroidal fluid', 'short_desc': ''},
        {'code': '67025', 'category': 'Surgery', 'paraphrased_desc': 'Injection of vitreous substitute', 'short_desc': ''},
        {'code': '67027', 'category': 'Surgery', 'paraphrased_desc': 'Injection of vitreous substitute with aspiration', 'short_desc': ''},
        {'code': '67028', 'category': 'Surgery', 'paraphrased_desc': 'Injection of drug into eye', 'short_desc': ''},
        {'code': '67030', 'category': 'Surgery', 'paraphrased_desc': 'Discission of vitreous strands', 'short_desc': ''},
        {'code': '67031', 'category': 'Surgery', 'paraphrased_desc': 'Severing of vitreous strands by laser surgery', 'short_desc': ''},
        {'code': '67036', 'category': 'Surgery', 'paraphrased_desc': 'Vitrectomy with focal endolaser photocoagulation', 'short_desc': ''},
        {'code': '67039', 'category': 'Surgery', 'paraphrased_desc': 'Vitrectomy with focal endolaser photocoagulation and prophylaxis of retinal detachment', 'short_desc': ''},
        {'code': '67040', 'category': 'Surgery', 'paraphrased_desc': 'Vitrectomy with endolaser panretinal photocoagulation', 'short_desc': ''},
        {'code': '67041', 'category': 'Surgery', 'paraphrased_desc': 'Vitrectomy with removal of preretinal cellular membrane', 'short_desc': ''},
        {'code': '67042', 'category': 'Surgery', 'paraphrased_desc': 'Vitrectomy with removal of internal limiting membrane', 'short_desc': ''},
        {'code': '67043', 'category': 'Surgery', 'paraphrased_desc': 'Vitrectomy with removal of subretinal membrane', 'short_desc': ''},
        {'code': '67108', 'category': 'Surgery', 'paraphrased_desc': 'Repair of retinal detachment with diathermy', 'short_desc': ''},
        {'code': '67110', 'category': 'Surgery', 'paraphrased_desc': 'Repair of retinal detachment with photocoagulation', 'short_desc': ''},
        {'code': '67112', 'category': 'Surgery', 'paraphrased_desc': 'Repair of retinal detachment with cryotherapy', 'short_desc': ''},
        {'code': '67113', 'category': 'Surgery', 'paraphrased_desc': 'Repair of retinal detachment with photocoagulation and cryotherapy', 'short_desc': ''},
        {'code': '67115', 'category': 'Surgery', 'paraphrased_desc': 'Release of encircling material from previous surgery', 'short_desc': ''},
        {'code': '67120', 'category': 'Surgery', 'paraphrased_desc': 'Removal of implanted material from posterior segment of eye', 'short_desc': ''},
        {'code': '67121', 'category': 'Surgery', 'paraphrased_desc': 'Removal of implanted material from posterior segment of eye with vitrectomy', 'short_desc': ''},
        {'code': '67141', 'category': 'Surgery', 'paraphrased_desc': 'Prophylaxis of retinal detachment with diathermy', 'short_desc': ''},
        {'code': '67145', 'category': 'Surgery', 'paraphrased_desc': 'Prophylaxis of retinal detachment with photocoagulation', 'short_desc': ''},
        {'code': '67208', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of localized lesion of retina by cryotherapy', 'short_desc': ''},
        {'code': '67210', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of localized lesion of retina by photocoagulation', 'short_desc': ''},
        {'code': '67218', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of localized lesion of retina by radiation', 'short_desc': ''},
        {'code': '67220', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of localized lesion of choroid by photocoagulation', 'short_desc': ''},
        {'code': '67221', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of localized lesion of choroid by photodynamic therapy', 'short_desc': ''},
        {'code': '67225', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of localized lesion of choroid by radiation', 'short_desc': ''},
        {'code': '67227', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of extensive or progressive retinopathy by cryotherapy', 'short_desc': ''},
        {'code': '67228', 'category': 'Surgery', 'paraphrased_desc': 'Destruction of extensive or progressive retinopathy by photocoagulation', 'short_desc': ''},
    ])

    # EXPANSION: Cardiovascular procedures
    codes.extend([
        {'code': '92950', 'category': 'Surgery', 'paraphrased_desc': 'Cardiopulmonary resuscitation', 'short_desc': ''},
        {'code': '92953', 'category': 'Surgery', 'paraphrased_desc': 'Temporary transcutaneous pacing', 'short_desc': ''},
        {'code': '92960', 'category': 'Surgery', 'paraphrased_desc': 'Cardioversion, elective, external', 'short_desc': ''},
        {'code': '92961', 'category': 'Surgery', 'paraphrased_desc': 'Cardioversion, elective, internal', 'short_desc': ''},
        {'code': '92970', 'category': 'Surgery', 'paraphrased_desc': 'Cardioassist, internal', 'short_desc': ''},
        {'code': '92971', 'category': 'Surgery', 'paraphrased_desc': 'Cardioassist, external', 'short_desc': ''},
        {'code': '92975', 'category': 'Surgery', 'paraphrased_desc': 'Thrombolysis, coronary, by intracoronary infusion', 'short_desc': ''},
        {'code': '92977', 'category': 'Surgery', 'paraphrased_desc': 'Thrombolysis, coronary, by intravenous infusion', 'short_desc': ''},
        {'code': '92978', 'category': 'Surgery', 'paraphrased_desc': 'Endoluminal imaging of coronary vessel or graft', 'short_desc': ''},
        {'code': '92979', 'category': 'Surgery', 'paraphrased_desc': 'Endoluminal imaging of coronary vessel or graft, each additional vessel', 'short_desc': ''},
        {'code': '92986', 'category': 'Surgery', 'paraphrased_desc': 'Percutaneous balloon valvuloplasty, aortic valve', 'short_desc': ''},
        {'code': '92987', 'category': 'Surgery', 'paraphrased_desc': 'Percutaneous balloon valvuloplasty, mitral valve', 'short_desc': ''},
        {'code': '92990', 'category': 'Surgery', 'paraphrased_desc': 'Percutaneous balloon valvuloplasty, pulmonary valve', 'short_desc': ''},
        {'code': '92992', 'category': 'Surgery', 'paraphrased_desc': 'Atrial septectomy or septostomy', 'short_desc': ''},
        {'code': '92993', 'category': 'Surgery', 'paraphrased_desc': 'Atrial septectomy or septostomy, transvenous method', 'short_desc': ''},
        {'code': '92997', 'category': 'Surgery', 'paraphrased_desc': 'Percutaneous transluminal pulmonary artery balloon angioplasty, single vessel', 'short_desc': ''},
        {'code': '92998', 'category': 'Surgery', 'paraphrased_desc': 'Percutaneous transluminal pulmonary artery balloon angioplasty, each additional vessel', 'short_desc': ''},
        {'code': '93000', 'category': 'Surgery', 'paraphrased_desc': 'Electrocardiogram, routine, with interpretation and report', 'short_desc': ''},
        {'code': '93005', 'category': 'Surgery', 'paraphrased_desc': 'Electrocardiogram, routine, tracing only', 'short_desc': ''},
        {'code': '93010', 'category': 'Surgery', 'paraphrased_desc': 'Electrocardiogram, routine, interpretation and report only', 'short_desc': ''},
        {'code': '93015', 'category': 'Surgery', 'paraphrased_desc': 'Cardiovascular stress test with electrocardiogram', 'short_desc': ''},
        {'code': '93016', 'category': 'Surgery', 'paraphrased_desc': 'Cardiovascular stress test with electrocardiogram, supervision only', 'short_desc': ''},
        {'code': '93017', 'category': 'Surgery', 'paraphrased_desc': 'Cardiovascular stress test with electrocardiogram, tracing only', 'short_desc': ''},
        {'code': '93018', 'category': 'Surgery', 'paraphrased_desc': 'Cardiovascular stress test with electrocardiogram, interpretation and report only', 'short_desc': ''},
        {'code': '93040', 'category': 'Surgery', 'paraphrased_desc': 'Rhythm electrocardiogram, 1-3 leads with interpretation and report', 'short_desc': ''},
        {'code': '93041', 'category': 'Surgery', 'paraphrased_desc': 'Rhythm electrocardiogram, 1-3 leads, tracing only', 'short_desc': ''},
        {'code': '93042', 'category': 'Surgery', 'paraphrased_desc': 'Rhythm electrocardiogram, 1-3 leads, interpretation and report only', 'short_desc': ''},
        {'code': '93224', 'category': 'Surgery', 'paraphrased_desc': 'External electrocardiographic recording for 24 hours', 'short_desc': ''},
        {'code': '93225', 'category': 'Surgery', 'paraphrased_desc': 'External electrocardiographic recording for 24 hours with scanning analysis', 'short_desc': ''},
        {'code': '93226', 'category': 'Surgery', 'paraphrased_desc': 'External electrocardiographic recording for 24 hours with scanning analysis and report', 'short_desc': ''},
        {'code': '93227', 'category': 'Surgery', 'paraphrased_desc': 'External electrocardiographic recording for 24 hours with report', 'short_desc': ''},
        {'code': '93228', 'category': 'Surgery', 'paraphrased_desc': 'External electrocardiographic recording for 24 hours with analysis', 'short_desc': ''},
        {'code': '93229', 'category': 'Surgery', 'paraphrased_desc': 'External electrocardiographic recording for 24 hours with interpretation and report', 'short_desc': ''},
        {'code': '93260', 'category': 'Surgery', 'paraphrased_desc': 'Pacemaker or pacing cardioverter-defibrillator programming, single chamber', 'short_desc': ''},
        {'code': '93261', 'category': 'Surgery', 'paraphrased_desc': 'Pacemaker or pacing cardioverter-defibrillator programming, dual chamber', 'short_desc': ''},
        {'code': '93264', 'category': 'Surgery', 'paraphrased_desc': 'Remote monitoring of pacemaker or pacing cardioverter-defibrillator', 'short_desc': ''},
        {'code': '93279', 'category': 'Surgery', 'paraphrased_desc': 'Programming of implantable cardioverter-defibrillator', 'short_desc': ''},
        {'code': '93280', 'category': 'Surgery', 'paraphrased_desc': 'Programming of implantable cardioverter-defibrillator with testing', 'short_desc': ''},
        {'code': '93281', 'category': 'Surgery', 'paraphrased_desc': 'Programming of implantable cardioverter-defibrillator with testing and analysis', 'short_desc': ''},
        {'code': '93282', 'category': 'Surgery', 'paraphrased_desc': 'Programming of implantable cardioverter-defibrillator with testing, analysis, and report', 'short_desc': ''},
        {'code': '93283', 'category': 'Surgery', 'paraphrased_desc': 'Programming of implantable cardioverter-defibrillator with testing and electrophysiologic evaluation', 'short_desc': ''},
        {'code': '93284', 'category': 'Surgery', 'paraphrased_desc': 'Programming of subcutaneous implantable cardioverter-defibrillator', 'short_desc': ''},
        {'code': '93285', 'category': 'Surgery', 'paraphrased_desc': 'Programming of implantable loop recorder', 'short_desc': ''},
        {'code': '93286', 'category': 'Surgery', 'paraphrased_desc': 'Peri-procedural device evaluation of cardiovascular physiologic monitor', 'short_desc': ''},
        {'code': '93287', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of cardiovascular physiologic monitor with analysis and report', 'short_desc': ''},
        {'code': '93288', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of implantable cardioverter-defibrillator with analysis', 'short_desc': ''},
        {'code': '93289', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of implantable cardioverter-defibrillator with analysis and report', 'short_desc': ''},
        {'code': '93290', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of implantable cardioverter-defibrillator with programming', 'short_desc': ''},
        {'code': '93291', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of implantable loop recorder', 'short_desc': ''},
        {'code': '93292', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of wearable defibrillator', 'short_desc': ''},
        {'code': '93293', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of dual chamber pacemaker', 'short_desc': ''},
        {'code': '93294', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of single chamber pacemaker', 'short_desc': ''},
        {'code': '93295', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of single lead pacemaker', 'short_desc': ''},
        {'code': '93296', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of dual chamber pacemaker or pacing cardioverter-defibrillator', 'short_desc': ''},
        {'code': '93297', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of single chamber pacemaker or pacing cardioverter-defibrillator', 'short_desc': ''},
        {'code': '93298', 'category': 'Surgery', 'paraphrased_desc': 'Interrogation device evaluation of single or dual chamber pacemaker or subcutaneous cardiac rhythm monitor', 'short_desc': ''},
        {'code': '93303', 'category': 'Surgery', 'paraphrased_desc': 'Transthoracic echocardiography', 'short_desc': ''},
        {'code': '93304', 'category': 'Surgery', 'paraphrased_desc': 'Transthoracic echocardiography with Doppler', 'short_desc': ''},
        {'code': '93306', 'category': 'Surgery', 'paraphrased_desc': 'Transthoracic echocardiography, complete', 'short_desc': ''},
        {'code': '93307', 'category': 'Surgery', 'paraphrased_desc': 'Transthoracic echocardiography, complete with spectral and color Doppler', 'short_desc': ''},
        {'code': '93308', 'category': 'Surgery', 'paraphrased_desc': 'Transthoracic echocardiography, follow-up or limited study', 'short_desc': ''},
        {'code': '93312', 'category': 'Surgery', 'paraphrased_desc': 'Transesophageal echocardiography', 'short_desc': ''},
        {'code': '93313', 'category': 'Surgery', 'paraphrased_desc': 'Transesophageal echocardiography with probe placement', 'short_desc': ''},
        {'code': '93314', 'category': 'Surgery', 'paraphrased_desc': 'Transesophageal echocardiography with image acquisition', 'short_desc': ''},
        {'code': '93315', 'category': 'Surgery', 'paraphrased_desc': 'Transesophageal echocardiography with interpretation and report', 'short_desc': ''},
        {'code': '93316', 'category': 'Surgery', 'paraphrased_desc': 'Transesophageal echocardiography with color Doppler', 'short_desc': ''},
        {'code': '93317', 'category': 'Surgery', 'paraphrased_desc': 'Transesophageal echocardiography with pulsed wave Doppler', 'short_desc': ''},
        {'code': '93318', 'category': 'Surgery', 'paraphrased_desc': 'Transesophageal echocardiography with spectral Doppler', 'short_desc': ''},
        {'code': '93320', 'category': 'Surgery', 'paraphrased_desc': 'Doppler echocardiography, pulsed wave', 'short_desc': ''},
        {'code': '93321', 'category': 'Surgery', 'paraphrased_desc': 'Doppler echocardiography, pulsed wave with spectral display', 'short_desc': ''},
        {'code': '93325', 'category': 'Surgery', 'paraphrased_desc': 'Doppler echocardiography, color flow velocity mapping', 'short_desc': ''},
        {'code': '93350', 'category': 'Surgery', 'paraphrased_desc': 'Echocardiography with stress test', 'short_desc': ''},
        {'code': '93351', 'category': 'Surgery', 'paraphrased_desc': 'Echocardiography with stress test, including ECG', 'short_desc': ''},
        {'code': '93352', 'category': 'Surgery', 'paraphrased_desc': 'Echocardiography with stress test, including interpretation and report', 'short_desc': ''},
        {'code': '93355', 'category': 'Surgery', 'paraphrased_desc': 'Echocardiography, transesophageal, for congenital cardiac anomalies', 'short_desc': ''},
        {'code': '93356', 'category': 'Surgery', 'paraphrased_desc': 'Echocardiography, transesophageal, for congenital cardiac anomalies with probe placement', 'short_desc': ''},
    ])

    logger.info(f"Generated {len(codes)} Surgery codes")
    return codes


def generate_medicine_codes() -> List[Dict]:
    """Generate common Medicine codes 90000-99607

    Expanded to ~250 codes covering comprehensive medicine services.
    """
    codes = []

    # Immunizations - Vaccines
    codes.extend([
        {'code': '90630', 'category': 'Medicine', 'paraphrased_desc': 'Influenza virus vaccine, quadrivalent, intramuscular, preservative-free', 'short_desc': ''},
        {'code': '90658', 'category': 'Medicine', 'paraphrased_desc': 'Influenza virus vaccine, trivalent, intramuscular, age 3 and above', 'short_desc': ''},
        {'code': '90662', 'category': 'Medicine', 'paraphrased_desc': 'Influenza virus vaccine, high-dose, intramuscular', 'short_desc': ''},
        {'code': '90670', 'category': 'Medicine', 'paraphrased_desc': 'Pneumococcal conjugate vaccine (PCV13), intramuscular', 'short_desc': ''},
        {'code': '90732', 'category': 'Medicine', 'paraphrased_desc': 'Pneumococcal polysaccharide vaccine (PPSV23), subcutaneous or intramuscular', 'short_desc': ''},
        {'code': '90715', 'category': 'Medicine', 'paraphrased_desc': 'Tetanus, diphtheria toxoids, acellular pertussis (Tdap) vaccine', 'short_desc': ''},
        {'code': '90714', 'category': 'Medicine', 'paraphrased_desc': 'Tetanus and diphtheria (Td) vaccine, age 7 and above', 'short_desc': ''},
        {'code': '90471', 'category': 'Medicine', 'paraphrased_desc': 'Immunization administration, first vaccine/toxoid', 'short_desc': ''},
        {'code': '90472', 'category': 'Medicine', 'paraphrased_desc': 'Immunization administration, each additional vaccine/toxoid', 'short_desc': ''},
        {'code': '90460', 'category': 'Medicine', 'paraphrased_desc': 'Immunization counseling and administration, first component', 'short_desc': ''},
        {'code': '90461', 'category': 'Medicine', 'paraphrased_desc': 'Immunization counseling and administration, each additional component', 'short_desc': ''},
    ])

    # COVID-19 vaccines
    codes.extend([
        {'code': '91300', 'category': 'Medicine', 'paraphrased_desc': 'COVID-19 vaccine administration, first dose', 'short_desc': ''},
        {'code': '91301', 'category': 'Medicine', 'paraphrased_desc': 'COVID-19 vaccine administration, second dose', 'short_desc': ''},
        {'code': '91302', 'category': 'Medicine', 'paraphrased_desc': 'COVID-19 vaccine administration, third dose', 'short_desc': ''},
        {'code': '91303', 'category': 'Medicine', 'paraphrased_desc': 'COVID-19 vaccine administration, booster dose', 'short_desc': ''},
    ])

    # Therapeutic injections
    codes.extend([
        {'code': '96372', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic, prophylactic, or diagnostic injection, subcutaneous or intramuscular', 'short_desc': ''},
        {'code': '96374', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic, prophylactic, or diagnostic injection, intravenous push', 'short_desc': ''},
        {'code': '96365', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy, first hour', 'short_desc': ''},
        {'code': '96366', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy, each additional hour', 'short_desc': ''},
    ])

    # Chemotherapy administration
    codes.extend([
        {'code': '96401', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, subcutaneous or intramuscular', 'short_desc': ''},
        {'code': '96409', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous push', 'short_desc': ''},
        {'code': '96413', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous infusion, first hour', 'short_desc': ''},
    ])

    # Physical medicine - Therapeutic procedures
    codes.extend([
        {'code': '97110', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic exercise, each 15 minutes', 'short_desc': ''},
        {'code': '97112', 'category': 'Medicine', 'paraphrased_desc': 'Neuromuscular reeducation, each 15 minutes', 'short_desc': ''},
        {'code': '97116', 'category': 'Medicine', 'paraphrased_desc': 'Gait training, each 15 minutes', 'short_desc': ''},
        {'code': '97140', 'category': 'Medicine', 'paraphrased_desc': 'Manual therapy techniques, each 15 minutes', 'short_desc': ''},
        {'code': '97530', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic activities for functional performance, each 15 minutes', 'short_desc': ''},
    ])

    # Modalities
    codes.extend([
        {'code': '97010', 'category': 'Medicine', 'paraphrased_desc': 'Hot or cold packs therapy', 'short_desc': ''},
        {'code': '97012', 'category': 'Medicine', 'paraphrased_desc': 'Mechanical traction therapy', 'short_desc': ''},
        {'code': '97014', 'category': 'Medicine', 'paraphrased_desc': 'Electrical stimulation therapy', 'short_desc': ''},
        {'code': '97016', 'category': 'Medicine', 'paraphrased_desc': 'Vasopneumatic devices therapy', 'short_desc': ''},
        {'code': '97032', 'category': 'Medicine', 'paraphrased_desc': 'Electrical stimulation, manual, each 15 minutes', 'short_desc': ''},
        {'code': '97035', 'category': 'Medicine', 'paraphrased_desc': 'Ultrasound therapy, each 15 minutes', 'short_desc': ''},
    ])

    # Occupational therapy
    codes.extend([
        {'code': '97165', 'category': 'Medicine', 'paraphrased_desc': 'Occupational therapy evaluation, low complexity', 'short_desc': ''},
        {'code': '97166', 'category': 'Medicine', 'paraphrased_desc': 'Occupational therapy evaluation, moderate complexity', 'short_desc': ''},
        {'code': '97167', 'category': 'Medicine', 'paraphrased_desc': 'Occupational therapy evaluation, high complexity', 'short_desc': ''},
    ])

    # Physical therapy evaluation
    codes.extend([
        {'code': '97161', 'category': 'Medicine', 'paraphrased_desc': 'Physical therapy evaluation, low complexity', 'short_desc': ''},
        {'code': '97162', 'category': 'Medicine', 'paraphrased_desc': 'Physical therapy evaluation, moderate complexity', 'short_desc': ''},
        {'code': '97163', 'category': 'Medicine', 'paraphrased_desc': 'Physical therapy evaluation, high complexity', 'short_desc': ''},
    ])

    # Cardiac services
    codes.extend([
        {'code': '93000', 'category': 'Medicine', 'paraphrased_desc': 'Electrocardiogram (ECG), complete with interpretation and report', 'short_desc': ''},
        {'code': '93005', 'category': 'Medicine', 'paraphrased_desc': 'Electrocardiogram (ECG), tracing only', 'short_desc': ''},
        {'code': '93010', 'category': 'Medicine', 'paraphrased_desc': 'Electrocardiogram (ECG), interpretation and report only', 'short_desc': ''},
        {'code': '93015', 'category': 'Medicine', 'paraphrased_desc': 'Cardiovascular stress test with ECG monitoring, physician supervision', 'short_desc': ''},
        {'code': '93306', 'category': 'Medicine', 'paraphrased_desc': 'Echocardiography, complete transthoracic', 'short_desc': ''},
        {'code': '93350', 'category': 'Medicine', 'paraphrased_desc': 'Echocardiography with stress test', 'short_desc': ''},
    ])

    # Pulmonary function tests
    codes.extend([
        {'code': '94010', 'category': 'Medicine', 'paraphrased_desc': 'Spirometry with graphic record', 'short_desc': ''},
        {'code': '94060', 'category': 'Medicine', 'paraphrased_desc': 'Bronchodilation responsiveness, spirometry before and after bronchodilator', 'short_desc': ''},
    ])

    # Sleep studies
    codes.extend([
        {'code': '95810', 'category': 'Medicine', 'paraphrased_desc': 'Polysomnography, sleep staging with respiratory effort, oxygen saturation, and heart rate', 'short_desc': ''},
        {'code': '95811', 'category': 'Medicine', 'paraphrased_desc': 'Polysomnography, extended parameters with CPAP or BiPAP titration', 'short_desc': ''},
    ])

    # Nebulizer treatment (94640)
    codes.append({
        'code': '94640',
        'category': 'Medicine',
        'paraphrased_desc': 'Inhalation treatment for airway obstruction with nebulizer',
        'short_desc': '',
    })

    # EXPANSION: Additional childhood vaccines
    codes.extend([
        {'code': '90633', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis A vaccine, pediatric/adolescent dosage, 2-dose schedule', 'short_desc': ''},
        {'code': '90636', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis A and hepatitis B vaccine (HepA-HepB), adult dosage', 'short_desc': ''},
        {'code': '90644', 'category': 'Medicine', 'paraphrased_desc': 'Meningococcal conjugate vaccine, serogroups C & Y and Haemophilus b', 'short_desc': ''},
        {'code': '90649', 'category': 'Medicine', 'paraphrased_desc': 'Human Papillomavirus vaccine, types 6, 11, 16, 18 (quadrivalent)', 'short_desc': ''},
        {'code': '90650', 'category': 'Medicine', 'paraphrased_desc': 'Human Papillomavirus vaccine, types 16, 18, bivalent', 'short_desc': ''},
        {'code': '90651', 'category': 'Medicine', 'paraphrased_desc': 'Human Papillomavirus vaccine, types 6, 11, 16, 18, 31, 33, 45, 52, 58 (9-valent)', 'short_desc': ''},
        {'code': '90672', 'category': 'Medicine', 'paraphrased_desc': 'Influenza virus vaccine, quadrivalent, live, for intranasal use', 'short_desc': ''},
        {'code': '90675', 'category': 'Medicine', 'paraphrased_desc': 'Rabies vaccine, for intramuscular use', 'short_desc': ''},
        {'code': '90676', 'category': 'Medicine', 'paraphrased_desc': 'Rabies vaccine, for intradermal use', 'short_desc': ''},
        {'code': '90680', 'category': 'Medicine', 'paraphrased_desc': 'Rotavirus vaccine, pentavalent, 3-dose schedule', 'short_desc': ''},
        {'code': '90681', 'category': 'Medicine', 'paraphrased_desc': 'Rotavirus vaccine, human, attenuated, 2-dose schedule', 'short_desc': ''},
        {'code': '90687', 'category': 'Medicine', 'paraphrased_desc': 'Influenza virus vaccine, quadrivalent, split virus, when administered to children', 'short_desc': ''},
        {'code': '90696', 'category': 'Medicine', 'paraphrased_desc': 'Diphtheria, tetanus toxoids, acellular pertussis vaccine and inactivated poliovirus vaccine (DTaP-IPV)', 'short_desc': ''},
        {'code': '90697', 'category': 'Medicine', 'paraphrased_desc': 'Diphtheria, tetanus toxoids, acellular pertussis vaccine, inactivated poliovirus vaccine, Haemophilus influenzae type b PRP-OMP conjugate vaccine, and hepatitis B vaccine (DTaP-IPV-Hib-HepB)', 'short_desc': ''},
        {'code': '90698', 'category': 'Medicine', 'paraphrased_desc': 'Diphtheria, tetanus toxoids, acellular pertussis vaccine, Haemophilus influenzae type b, and inactivated poliovirus vaccine (DTaP-IPV/Hib)', 'short_desc': ''},
        {'code': '90700', 'category': 'Medicine', 'paraphrased_desc': 'Diphtheria, tetanus toxoids, and acellular pertussis vaccine (DTaP)', 'short_desc': ''},
        {'code': '90702', 'category': 'Medicine', 'paraphrased_desc': 'Diphtheria and tetanus toxoids adsorbed (DT), pediatric', 'short_desc': ''},
        {'code': '90707', 'category': 'Medicine', 'paraphrased_desc': 'Measles, mumps and rubella virus vaccine (MMR), live', 'short_desc': ''},
        {'code': '90710', 'category': 'Medicine', 'paraphrased_desc': 'Measles, mumps, rubella, and varicella vaccine (MMRV), live', 'short_desc': ''},
        {'code': '90712', 'category': 'Medicine', 'paraphrased_desc': 'Poliovirus vaccine, live, oral', 'short_desc': ''},
        {'code': '90713', 'category': 'Medicine', 'paraphrased_desc': 'Poliovirus vaccine, inactivated (IPV), for subcutaneous or intramuscular use', 'short_desc': ''},
        {'code': '90716', 'category': 'Medicine', 'paraphrased_desc': 'Varicella virus vaccine (VAR), live', 'short_desc': ''},
        {'code': '90723', 'category': 'Medicine', 'paraphrased_desc': 'Diphtheria, tetanus toxoids, acellular pertussis vaccine, hepatitis B, and inactivated poliovirus vaccine (DTaP-HepB-IPV)', 'short_desc': ''},
        {'code': '90733', 'category': 'Medicine', 'paraphrased_desc': 'Meningococcal polysaccharide vaccine, serogroups A, C, Y, W-135', 'short_desc': ''},
        {'code': '90734', 'category': 'Medicine', 'paraphrased_desc': 'Meningococcal conjugate vaccine, serogroups A, C, W-135, Y', 'short_desc': ''},
        {'code': '90736', 'category': 'Medicine', 'paraphrased_desc': 'Zoster (shingles) vaccine, live, for subcutaneous injection', 'short_desc': ''},
        {'code': '90738', 'category': 'Medicine', 'paraphrased_desc': 'Japanese encephalitis virus vaccine', 'short_desc': ''},
        {'code': '90739', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis B vaccine (HepB), adult dosage', 'short_desc': ''},
        {'code': '90740', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis B vaccine (HepB), dialysis or immunosuppressed patient dosage', 'short_desc': ''},
        {'code': '90743', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis B vaccine (HepB), adolescent dosage', 'short_desc': ''},
        {'code': '90744', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis B vaccine (HepB), pediatric/adolescent dosage', 'short_desc': ''},
        {'code': '90746', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis B vaccine (HepB), adult dosage', 'short_desc': ''},
        {'code': '90747', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis B vaccine (HepB), dialysis or immunosuppressed patient dosage', 'short_desc': ''},
        {'code': '90748', 'category': 'Medicine', 'paraphrased_desc': 'Hepatitis B and Haemophilus influenzae b vaccine (Hib-HepB)', 'short_desc': ''},
        {'code': '90750', 'category': 'Medicine', 'paraphrased_desc': 'Zoster (shingles) vaccine, recombinant', 'short_desc': ''},
        {'code': '90756', 'category': 'Medicine', 'paraphrased_desc': 'Influenza virus vaccine, quadrivalent, intradermal', 'short_desc': ''},
        {'code': '90785', 'category': 'Medicine', 'paraphrased_desc': 'Interactive complexity psychotherapy add-on', 'short_desc': ''},
        {'code': '90791', 'category': 'Medicine', 'paraphrased_desc': 'Psychiatric diagnostic evaluation', 'short_desc': ''},
        {'code': '90792', 'category': 'Medicine', 'paraphrased_desc': 'Psychiatric diagnostic evaluation with medical services', 'short_desc': ''},
        {'code': '90832', 'category': 'Medicine', 'paraphrased_desc': 'Psychotherapy, 30 minutes with patient', 'short_desc': ''},
        {'code': '90834', 'category': 'Medicine', 'paraphrased_desc': 'Psychotherapy, 45 minutes with patient', 'short_desc': ''},
        {'code': '90837', 'category': 'Medicine', 'paraphrased_desc': 'Psychotherapy, 60 minutes with patient', 'short_desc': ''},
        {'code': '90839', 'category': 'Medicine', 'paraphrased_desc': 'Psychotherapy for crisis, first 60 minutes', 'short_desc': ''},
        {'code': '90840', 'category': 'Medicine', 'paraphrased_desc': 'Psychotherapy for crisis, each additional 30 minutes', 'short_desc': ''},
        {'code': '90845', 'category': 'Medicine', 'paraphrased_desc': 'Psychoanalysis', 'short_desc': ''},
        {'code': '90846', 'category': 'Medicine', 'paraphrased_desc': 'Family psychotherapy without patient present', 'short_desc': ''},
        {'code': '90847', 'category': 'Medicine', 'paraphrased_desc': 'Family psychotherapy with patient present', 'short_desc': ''},
        {'code': '90849', 'category': 'Medicine', 'paraphrased_desc': 'Multiple-family group psychotherapy', 'short_desc': ''},
        {'code': '90853', 'category': 'Medicine', 'paraphrased_desc': 'Group psychotherapy', 'short_desc': ''},
    ])

    # EXPANSION: Additional diagnostic tests
    codes.extend([
        {'code': '92002', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmological services, medical examination and evaluation, intermediate, new patient', 'short_desc': ''},
        {'code': '92004', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmological services, medical examination and evaluation, comprehensive, new patient', 'short_desc': ''},
        {'code': '92012', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmological services, medical examination and evaluation, intermediate, established patient', 'short_desc': ''},
        {'code': '92014', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmological services, medical examination and evaluation, comprehensive, established patient', 'short_desc': ''},
        {'code': '92015', 'category': 'Medicine', 'paraphrased_desc': 'Determination of refractive state', 'short_desc': ''},
        {'code': '92018', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmological examination and evaluation, under general anesthesia', 'short_desc': ''},
        {'code': '92019', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmological examination and evaluation, under general anesthesia, with manipulation of globe', 'short_desc': ''},
        {'code': '92025', 'category': 'Medicine', 'paraphrased_desc': 'Computerized corneal topography, unilateral or bilateral', 'short_desc': ''},
        {'code': '92060', 'category': 'Medicine', 'paraphrased_desc': 'Sensorimotor examination with multiple measurements of ocular deviation', 'short_desc': ''},
        {'code': '92065', 'category': 'Medicine', 'paraphrased_desc': 'Orthoptic training', 'short_desc': ''},
        {'code': '92071', 'category': 'Medicine', 'paraphrased_desc': 'Fitting of contact lens for treatment of ocular surface disease', 'short_desc': ''},
        {'code': '92072', 'category': 'Medicine', 'paraphrased_desc': 'Fitting of contact lens for management of keratoconus, initial fitting', 'short_desc': ''},
        {'code': '92081', 'category': 'Medicine', 'paraphrased_desc': 'Visual field examination, unilateral or bilateral', 'short_desc': ''},
        {'code': '92082', 'category': 'Medicine', 'paraphrased_desc': 'Visual field examination, unilateral or bilateral, with interpretation and report', 'short_desc': ''},
        {'code': '92083', 'category': 'Medicine', 'paraphrased_desc': 'Visual field examination, unilateral or bilateral, extended', 'short_desc': ''},
        {'code': '92100', 'category': 'Medicine', 'paraphrased_desc': 'Serial tonometry with multiple measurements', 'short_desc': ''},
        {'code': '92132', 'category': 'Medicine', 'paraphrased_desc': 'Scanning computerized ophthalmic diagnostic imaging, anterior segment', 'short_desc': ''},
        {'code': '92133', 'category': 'Medicine', 'paraphrased_desc': 'Scanning computerized ophthalmic diagnostic imaging, posterior segment', 'short_desc': ''},
        {'code': '92134', 'category': 'Medicine', 'paraphrased_desc': 'Scanning computerized ophthalmic diagnostic imaging, posterior segment, with interpretation and report', 'short_desc': ''},
        {'code': '92136', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmic biometry by partial coherence interferometry with intraocular lens power calculation', 'short_desc': ''},
        {'code': '92145', 'category': 'Medicine', 'paraphrased_desc': 'Corneal hysteresis determination, by air impulse stimulation', 'short_desc': ''},
        {'code': '92201', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmoscopy, extended, with retinal drawing', 'short_desc': ''},
        {'code': '92202', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmoscopy, extended, with drawing of optic nerve or macula', 'short_desc': ''},
        {'code': '92225', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmoscopy, extended, with retinal drawing and scleral depression', 'short_desc': ''},
        {'code': '92226', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmoscopy, extended, with drawing of optic nerve or macula and scleral depression', 'short_desc': ''},
        {'code': '92227', 'category': 'Medicine', 'paraphrased_desc': 'Remote imaging for detection of retinal disease', 'short_desc': ''},
        {'code': '92228', 'category': 'Medicine', 'paraphrased_desc': 'Remote imaging for monitoring and management of active retinal disease', 'short_desc': ''},
        {'code': '92229', 'category': 'Medicine', 'paraphrased_desc': 'Imaging of retina for detection or monitoring of disease', 'short_desc': ''},
        {'code': '92230', 'category': 'Medicine', 'paraphrased_desc': 'Fluorescein angioscopy', 'short_desc': ''},
        {'code': '92235', 'category': 'Medicine', 'paraphrased_desc': 'Fluorescein angiography', 'short_desc': ''},
        {'code': '92240', 'category': 'Medicine', 'paraphrased_desc': 'Indocyanine-green angiography', 'short_desc': ''},
        {'code': '92250', 'category': 'Medicine', 'paraphrased_desc': 'Fundus photography with interpretation and report', 'short_desc': ''},
        {'code': '92260', 'category': 'Medicine', 'paraphrased_desc': 'Ophthalmodynamometry', 'short_desc': ''},
        {'code': '92265', 'category': 'Medicine', 'paraphrased_desc': 'Needle oculoelectromyography, 1 or more extraocular muscles', 'short_desc': ''},
        {'code': '92270', 'category': 'Medicine', 'paraphrased_desc': 'Electro-oculography with interpretation and report', 'short_desc': ''},
        {'code': '92273', 'category': 'Medicine', 'paraphrased_desc': 'Electroretinography (ERG), with interpretation and report', 'short_desc': ''},
        {'code': '92274', 'category': 'Medicine', 'paraphrased_desc': 'Electroretinography (ERG), with interpretation and report, photo stress', 'short_desc': ''},
        {'code': '92283', 'category': 'Medicine', 'paraphrased_desc': 'Color vision examination, extended', 'short_desc': ''},
        {'code': '92284', 'category': 'Medicine', 'paraphrased_desc': 'Dark adaptation examination with interpretation and report', 'short_desc': ''},
        {'code': '92502', 'category': 'Medicine', 'paraphrased_desc': 'Otolaryngologic examination under general anesthesia', 'short_desc': ''},
        {'code': '92504', 'category': 'Medicine', 'paraphrased_desc': 'Binocular microscopy, separate diagnostic examination', 'short_desc': ''},
        {'code': '92507', 'category': 'Medicine', 'paraphrased_desc': 'Treatment of speech, language, voice, communication disorders', 'short_desc': ''},
        {'code': '92508', 'category': 'Medicine', 'paraphrased_desc': 'Treatment of speech, language, voice, communication disorders, group', 'short_desc': ''},
        {'code': '92511', 'category': 'Medicine', 'paraphrased_desc': 'Nasopharyngoscopy with endoscope', 'short_desc': ''},
        {'code': '92512', 'category': 'Medicine', 'paraphrased_desc': 'Nasal function studies', 'short_desc': ''},
        {'code': '92520', 'category': 'Medicine', 'paraphrased_desc': 'Laryngeal function studies', 'short_desc': ''},
        {'code': '92526', 'category': 'Medicine', 'paraphrased_desc': 'Treatment of swallowing dysfunction', 'short_desc': ''},
        {'code': '92537', 'category': 'Medicine', 'paraphrased_desc': 'Caloric vestibular test with recording, bilateral', 'short_desc': ''},
        {'code': '92540', 'category': 'Medicine', 'paraphrased_desc': 'Basic vestibular evaluation', 'short_desc': ''},
        {'code': '92541', 'category': 'Medicine', 'paraphrased_desc': 'Spontaneous nystagmus test with recording', 'short_desc': ''},
        {'code': '92542', 'category': 'Medicine', 'paraphrased_desc': 'Positional nystagmus test', 'short_desc': ''},
        {'code': '92543', 'category': 'Medicine', 'paraphrased_desc': 'Caloric vestibular test, each irrigation', 'short_desc': ''},
        {'code': '92544', 'category': 'Medicine', 'paraphrased_desc': 'Optokinetic nystagmus test', 'short_desc': ''},
        {'code': '92545', 'category': 'Medicine', 'paraphrased_desc': 'Oscillating tracking test', 'short_desc': ''},
        {'code': '92546', 'category': 'Medicine', 'paraphrased_desc': 'Sinusoidal vertical axis rotational testing', 'short_desc': ''},
        {'code': '92547', 'category': 'Medicine', 'paraphrased_desc': 'Use of vertical electrodes in nystagmus testing', 'short_desc': ''},
        {'code': '92548', 'category': 'Medicine', 'paraphrased_desc': 'Computerized dynamic posturography', 'short_desc': ''},
        {'code': '92550', 'category': 'Medicine', 'paraphrased_desc': 'Tympanometry', 'short_desc': ''},
        {'code': '92551', 'category': 'Medicine', 'paraphrased_desc': 'Pure tone audiometry (threshold), air only', 'short_desc': ''},
        {'code': '92552', 'category': 'Medicine', 'paraphrased_desc': 'Pure tone audiometry (threshold), air and bone', 'short_desc': ''},
        {'code': '92553', 'category': 'Medicine', 'paraphrased_desc': 'Pure tone audiometry (threshold), air only, automated', 'short_desc': ''},
        {'code': '92555', 'category': 'Medicine', 'paraphrased_desc': 'Speech audiometry threshold', 'short_desc': ''},
        {'code': '92556', 'category': 'Medicine', 'paraphrased_desc': 'Speech audiometry threshold with speech recognition', 'short_desc': ''},
        {'code': '92557', 'category': 'Medicine', 'paraphrased_desc': 'Comprehensive audiometry, air and bone', 'short_desc': ''},
        {'code': '92558', 'category': 'Medicine', 'paraphrased_desc': 'Evoked otoacoustic emissions, screening', 'short_desc': ''},
        {'code': '92559', 'category': 'Medicine', 'paraphrased_desc': 'Audiometric testing of groups', 'short_desc': ''},
        {'code': '92560', 'category': 'Medicine', 'paraphrased_desc': 'Bekesy audiometry, screening', 'short_desc': ''},
        {'code': '92561', 'category': 'Medicine', 'paraphrased_desc': 'Bekesy audiometry, diagnostic', 'short_desc': ''},
        {'code': '92562', 'category': 'Medicine', 'paraphrased_desc': 'Loudness balance test, alternate binaural or monaural', 'short_desc': ''},
        {'code': '92563', 'category': 'Medicine', 'paraphrased_desc': 'Tone decay test', 'short_desc': ''},
        {'code': '92564', 'category': 'Medicine', 'paraphrased_desc': 'Short increment sensitivity index (SISI)', 'short_desc': ''},
        {'code': '92565', 'category': 'Medicine', 'paraphrased_desc': 'Stenger test, pure tone', 'short_desc': ''},
        {'code': '92567', 'category': 'Medicine', 'paraphrased_desc': 'Tympanometry', 'short_desc': ''},
        {'code': '92568', 'category': 'Medicine', 'paraphrased_desc': 'Acoustic reflex testing, threshold', 'short_desc': ''},
        {'code': '92570', 'category': 'Medicine', 'paraphrased_desc': 'Acoustic immittance testing', 'short_desc': ''},
        {'code': '92571', 'category': 'Medicine', 'paraphrased_desc': 'Filtered speech test', 'short_desc': ''},
        {'code': '92572', 'category': 'Medicine', 'paraphrased_desc': 'Staggered spondaic word test', 'short_desc': ''},
        {'code': '92575', 'category': 'Medicine', 'paraphrased_desc': 'Sensorineural acuity level test', 'short_desc': ''},
        {'code': '92576', 'category': 'Medicine', 'paraphrased_desc': 'Synthetic sentence identification test', 'short_desc': ''},
        {'code': '92577', 'category': 'Medicine', 'paraphrased_desc': 'Stenger test, speech', 'short_desc': ''},
        {'code': '92579', 'category': 'Medicine', 'paraphrased_desc': 'Visual reinforcement audiometry', 'short_desc': ''},
        {'code': '92582', 'category': 'Medicine', 'paraphrased_desc': 'Conditioning play audiometry', 'short_desc': ''},
        {'code': '92583', 'category': 'Medicine', 'paraphrased_desc': 'Select picture audiometry', 'short_desc': ''},
        {'code': '92584', 'category': 'Medicine', 'paraphrased_desc': 'Electrocochleography', 'short_desc': ''},
        {'code': '92585', 'category': 'Medicine', 'paraphrased_desc': 'Auditory evoked potentials for evoked response audiometry', 'short_desc': ''},
        {'code': '92586', 'category': 'Medicine', 'paraphrased_desc': 'Auditory evoked potentials for evoked response audiometry, limited', 'short_desc': ''},
        {'code': '92587', 'category': 'Medicine', 'paraphrased_desc': 'Distortion product evoked otoacoustic emissions, limited', 'short_desc': ''},
        {'code': '92588', 'category': 'Medicine', 'paraphrased_desc': 'Distortion product evoked otoacoustic emissions, comprehensive', 'short_desc': ''},
        {'code': '92601', 'category': 'Medicine', 'paraphrased_desc': 'Diagnostic analysis of cochlear implant, first hour', 'short_desc': ''},
        {'code': '92602', 'category': 'Medicine', 'paraphrased_desc': 'Diagnostic analysis of cochlear implant, subsequent hour', 'short_desc': ''},
        {'code': '92603', 'category': 'Medicine', 'paraphrased_desc': 'Diagnostic analysis of auditory brainstem implant, first hour', 'short_desc': ''},
        {'code': '92604', 'category': 'Medicine', 'paraphrased_desc': 'Diagnostic analysis of auditory brainstem implant, subsequent hour', 'short_desc': ''},
        {'code': '96360', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy/diagnosis, initial hour', 'short_desc': ''},
        {'code': '96361', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy/diagnosis, each additional hour', 'short_desc': ''},
        {'code': '96365', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy/prophylaxis/diagnosis, initial hour', 'short_desc': ''},
        {'code': '96366', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy/prophylaxis/diagnosis, each additional hour', 'short_desc': ''},
        {'code': '96367', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy/prophylaxis/diagnosis, additional sequential infusion', 'short_desc': ''},
        {'code': '96368', 'category': 'Medicine', 'paraphrased_desc': 'Intravenous infusion for therapy/prophylaxis/diagnosis, concurrent infusion', 'short_desc': ''},
        {'code': '96369', 'category': 'Medicine', 'paraphrased_desc': 'Subcutaneous infusion for therapy/prophylaxis/diagnosis, initial hour', 'short_desc': ''},
        {'code': '96370', 'category': 'Medicine', 'paraphrased_desc': 'Subcutaneous infusion for therapy/prophylaxis/diagnosis, each additional hour', 'short_desc': ''},
        {'code': '96371', 'category': 'Medicine', 'paraphrased_desc': 'Subcutaneous infusion for therapy/prophylaxis/diagnosis, additional pump setup', 'short_desc': ''},
        {'code': '96372', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic, prophylactic, or diagnostic injection, subcutaneous or intramuscular', 'short_desc': ''},
        {'code': '96373', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic, prophylactic, or diagnostic injection, intra-arterial', 'short_desc': ''},
        {'code': '96374', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic, prophylactic, or diagnostic injection, intravenous push', 'short_desc': ''},
        {'code': '96375', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic, prophylactic, or diagnostic injection, each additional sequential push', 'short_desc': ''},
        {'code': '96376', 'category': 'Medicine', 'paraphrased_desc': 'Therapeutic, prophylactic, or diagnostic injection, each additional sequential push of new substance', 'short_desc': ''},
        {'code': '96377', 'category': 'Medicine', 'paraphrased_desc': 'Application of on-body injector for timed subcutaneous injection', 'short_desc': ''},
        {'code': '96379', 'category': 'Medicine', 'paraphrased_desc': 'Unlisted therapeutic, prophylactic, or diagnostic intravenous or intra-arterial injection or infusion', 'short_desc': ''},
        {'code': '96401', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, subcutaneous or intramuscular, non-hormonal anti-neoplastic', 'short_desc': ''},
        {'code': '96402', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, subcutaneous or intramuscular, hormonal anti-neoplastic', 'short_desc': ''},
        {'code': '96405', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intralesional, up to and including 7 lesions', 'short_desc': ''},
        {'code': '96406', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intralesional, more than 7 lesions', 'short_desc': ''},
        {'code': '96409', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous, push technique, single or initial substance', 'short_desc': ''},
        {'code': '96411', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous, push technique, each additional substance', 'short_desc': ''},
        {'code': '96413', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous infusion, up to 1 hour', 'short_desc': ''},
        {'code': '96415', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous infusion, each additional hour', 'short_desc': ''},
        {'code': '96416', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous infusion, prolonged, initiation', 'short_desc': ''},
        {'code': '96417', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intravenous infusion, each additional sequential infusion', 'short_desc': ''},
        {'code': '96420', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intra-arterial, push technique', 'short_desc': ''},
        {'code': '96422', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intra-arterial infusion, up to 1 hour', 'short_desc': ''},
        {'code': '96423', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intra-arterial infusion, each additional hour', 'short_desc': ''},
        {'code': '96425', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration, intraperitoneal, via implanted port or catheter', 'short_desc': ''},
        {'code': '96440', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration into pleural cavity', 'short_desc': ''},
        {'code': '96446', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration into peritoneal cavity', 'short_desc': ''},
        {'code': '96450', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy administration into CNS', 'short_desc': ''},
        {'code': '96521', 'category': 'Medicine', 'paraphrased_desc': 'Refilling and maintenance of portable pump', 'short_desc': ''},
        {'code': '96522', 'category': 'Medicine', 'paraphrased_desc': 'Refilling and maintenance of implantable pump or reservoir for systemic drug delivery', 'short_desc': ''},
        {'code': '96523', 'category': 'Medicine', 'paraphrased_desc': 'Irrigation of implanted venous access port for drug delivery', 'short_desc': ''},
        {'code': '96542', 'category': 'Medicine', 'paraphrased_desc': 'Chemotherapy injection, subarachnoid or intraventricular', 'short_desc': ''},
    ])

    # EXPANSION: Dialysis
    codes.extend([
        {'code': '90935', 'category': 'Medicine', 'paraphrased_desc': 'Hemodialysis procedure with single physician evaluation', 'short_desc': ''},
        {'code': '90937', 'category': 'Medicine', 'paraphrased_desc': 'Hemodialysis procedure requiring repeated physician evaluations', 'short_desc': ''},
        {'code': '90940', 'category': 'Medicine', 'paraphrased_desc': 'Hemodialysis access flow study to determine blood flow', 'short_desc': ''},
        {'code': '90945', 'category': 'Medicine', 'paraphrased_desc': 'Dialysis procedure other than hemodialysis', 'short_desc': ''},
        {'code': '90947', 'category': 'Medicine', 'paraphrased_desc': 'Dialysis procedure other than hemodialysis, requiring repeated evaluations', 'short_desc': ''},
        {'code': '90951', 'category': 'Medicine', 'paraphrased_desc': 'End-stage renal disease services per day for patients younger than 2 years', 'short_desc': ''},
        {'code': '90952', 'category': 'Medicine', 'paraphrased_desc': 'End-stage renal disease services per day for patients 2-11 years', 'short_desc': ''},
        {'code': '90953', 'category': 'Medicine', 'paraphrased_desc': 'End-stage renal disease services per day for patients 12-19 years', 'short_desc': ''},
        {'code': '90954', 'category': 'Medicine', 'paraphrased_desc': 'End-stage renal disease services per day for patients 20 years and older', 'short_desc': ''},
    ])

    logger.info(f"Generated {len(codes)} Medicine codes")
    return codes


def generate_anesthesia_codes() -> List[Dict]:
    """Generate common Anesthesia codes 00100-01999

    Expanded to ~150 codes covering comprehensive anesthesia procedures.
    """
    codes = []

    # Head anesthesia
    codes.extend([
        {'code': '00100', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on salivary glands', 'short_desc': ''},
        {'code': '00102', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures involving plastic repair of cleft lip', 'short_desc': ''},
        {'code': '00103', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for reconstructive procedures of eyelid', 'short_desc': ''},
        {'code': '00104', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for electroconvulsive therapy', 'short_desc': ''},
        {'code': '00120', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on external, middle, and inner ear', 'short_desc': ''},
        {'code': '00140', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on eye', 'short_desc': ''},
        {'code': '00160', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on nose and accessory sinuses', 'short_desc': ''},
    ])

    # Neck anesthesia
    codes.extend([
        {'code': '00300', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all procedures on the integumentary system, muscles and nerves of head, neck, and posterior trunk', 'short_desc': ''},
        {'code': '00320', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all procedures on esophagus', 'short_desc': ''},
        {'code': '00350', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on major vessels of neck', 'short_desc': ''},
    ])

    # Thorax anesthesia
    codes.extend([
        {'code': '00400', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on the integumentary system on the extremities, anterior trunk and perineum', 'short_desc': ''},
        {'code': '00410', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on the integumentary system on the extremities, anterior trunk and perineum, radical or modified', 'short_desc': ''},
        {'code': '00500', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all procedures on esophagus', 'short_desc': ''},
        {'code': '00520', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for closed chest procedures', 'short_desc': ''},
        {'code': '00540', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for thoracotomy procedures involving lungs, pleura, thymus or mediastinum', 'short_desc': ''},
    ])

    # Spine and spinal cord
    codes.extend([
        {'code': '00600', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on cervical spine and cord', 'short_desc': ''},
        {'code': '00620', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on thoracic spine and cord', 'short_desc': ''},
        {'code': '00630', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures in lumbar region', 'short_desc': ''},
    ])

    # Upper abdomen
    codes.extend([
        {'code': '00700', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on upper abdominal anterior wall', 'short_desc': ''},
        {'code': '00730', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on upper abdomen, involving stomach', 'short_desc': ''},
        {'code': '00740', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for upper gastrointestinal endoscopic procedures', 'short_desc': ''},
        {'code': '00790', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for intraperitoneal procedures in upper abdomen', 'short_desc': ''},
    ])

    # Lower abdomen
    codes.extend([
        {'code': '00800', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on lower anterior abdominal wall', 'short_desc': ''},
        {'code': '00810', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for lower intestinal endoscopic procedures', 'short_desc': ''},
        {'code': '00840', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for intraperitoneal procedures in lower abdomen', 'short_desc': ''},
        {'code': '00860', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for extraperitoneal procedures in lower abdomen', 'short_desc': ''},
    ])

    # Perineum
    codes.extend([
        {'code': '00902', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for anorectal procedure', 'short_desc': ''},
        {'code': '00940', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for vaginal procedures', 'short_desc': ''},
        {'code': '00944', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for vaginal hysterectomy', 'short_desc': ''},
    ])

    # Pelvis
    codes.extend([
        {'code': '01112', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for bone marrow aspiration and/or biopsy, anterior or posterior iliac crest', 'short_desc': ''},
        {'code': '01120', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on bony pelvis', 'short_desc': ''},
        {'code': '01150', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for radical procedures for tumor of pelvis', 'short_desc': ''},
    ])

    # Upper leg
    codes.extend([
        {'code': '01200', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all closed procedures involving hip joint', 'short_desc': ''},
        {'code': '01202', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for arthroscopic procedures of hip joint', 'short_desc': ''},
        {'code': '01210', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for open procedures involving hip joint', 'short_desc': ''},
        {'code': '01214', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for total hip arthroplasty', 'short_desc': ''},
        {'code': '01220', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all closed procedures involving upper two-thirds of femur', 'short_desc': ''},
        {'code': '01230', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for open procedures involving upper two-thirds of femur', 'short_desc': ''},
    ])

    # Knee and popliteal area
    codes.extend([
        {'code': '01320', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all procedures on nerves, muscles, tendons, fascia, and bursae of knee and/or popliteal area', 'short_desc': ''},
        {'code': '01382', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for diagnostic arthroscopic procedures of knee joint', 'short_desc': ''},
        {'code': '01400', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for open or surgical arthroscopic procedures on knee joint', 'short_desc': ''},
        {'code': '01402', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for total knee arthroplasty', 'short_desc': ''},
    ])

    # Lower leg
    codes.extend([
        {'code': '01462', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all closed procedures on lower leg, ankle, and foot', 'short_desc': ''},
        {'code': '01464', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for arthroscopic procedures of ankle and/or foot', 'short_desc': ''},
        {'code': '01470', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on nerves, muscles, tendons, and fascia of lower leg, ankle, and foot', 'short_desc': ''},
        {'code': '01480', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for open procedures on bones of lower leg, ankle, and foot', 'short_desc': ''},
    ])

    # Shoulder and axilla
    codes.extend([
        {'code': '01610', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all procedures on nerves, muscles, tendons, fascia, and bursae of shoulder and axilla', 'short_desc': ''},
        {'code': '01620', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all closed procedures on humeral head and neck, sternoclavicular joint, acromioclavicular joint, and shoulder joint', 'short_desc': ''},
        {'code': '01630', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for open or surgical arthroscopic procedures on humeral head and neck, sternoclavicular joint, acromioclavicular joint, and shoulder joint', 'short_desc': ''},
        {'code': '01638', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for total shoulder replacement', 'short_desc': ''},
    ])

    # Upper arm and elbow
    codes.extend([
        {'code': '01710', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for procedures on nerves, muscles, tendons, fascia, and bursae of upper arm and elbow', 'short_desc': ''},
        {'code': '01730', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all closed procedures on humerus and elbow', 'short_desc': ''},
        {'code': '01740', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for open or surgical arthroscopic procedures of the elbow', 'short_desc': ''},
        {'code': '01742', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for total elbow replacement', 'short_desc': ''},
    ])

    # Forearm, wrist, and hand
    codes.extend([
        {'code': '01810', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all procedures on nerves, muscles, tendons, fascia, and bursae of forearm, wrist, and hand', 'short_desc': ''},
        {'code': '01820', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for all closed procedures on radius, ulna, wrist, or hand bones', 'short_desc': ''},
        {'code': '01830', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for open or surgical arthroscopic/endoscopic procedures on distal radius, ulna, wrist, or hand', 'short_desc': ''},
    ])

    # Obstetric
    codes.extend([
        {'code': '01960', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for vaginal delivery only', 'short_desc': ''},
        {'code': '01961', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for cesarean delivery only', 'short_desc': ''},
        {'code': '01962', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for urgent hysterectomy following delivery', 'short_desc': ''},
        {'code': '01963', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for cesarean hysterectomy without any labor analgesia/anesthesia care', 'short_desc': ''},
        {'code': '01967', 'category': 'Anesthesia', 'paraphrased_desc': 'Neuraxial labor analgesia/anesthesia for planned vaginal delivery', 'short_desc': ''},
        {'code': '01968', 'category': 'Anesthesia', 'paraphrased_desc': 'Anesthesia for cesarean delivery following neuraxial labor analgesia/anesthesia', 'short_desc': ''},
    ])

    logger.info(f"Generated {len(codes)} Anesthesia codes")
    return codes


def write_csv(codes: List[Dict], output_file: Path):
    """Write codes to CSV file

    Args:
        codes: List of code dictionaries
        output_file: Path to output CSV file
    """
    fieldnames = ['code', 'code_system', 'paraphrased_desc', 'short_desc', 'category', 'license_status', 'version_year']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for code in codes:
            writer.writerow({
                'code': code['code'],
                'code_system': 'CPT',
                'paraphrased_desc': code['paraphrased_desc'],
                'short_desc': code.get('short_desc', ''),
                'category': code['category'],
                'license_status': 'free',
                'version_year': '2025'
            })

    logger.info(f"Wrote {len(codes)} codes to {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate paraphrased CPT code descriptions"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_DIR / "cpt_2025_expanded.csv"),
        help="Output CSV file path"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show counts without writing file"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("CPT Paraphrased Code Generator")
    logger.info("=" * 70)
    logger.info(f"Output file: {args.output}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 70)
    logger.info("")

    # Generate all codes
    logger.info("Generating CPT codes...")
    logger.info("")

    all_codes = []

    # E/M codes (~60 codes)
    all_codes.extend(generate_em_codes())

    # Laboratory codes (~60 codes)
    all_codes.extend(generate_lab_codes())

    # Radiology codes (~80 codes)
    all_codes.extend(generate_radiology_codes())

    # Surgery codes (~70 codes)
    all_codes.extend(generate_surgery_codes())

    # Medicine codes (~50 codes)
    all_codes.extend(generate_medicine_codes())

    # Anesthesia codes (~70 codes)
    all_codes.extend(generate_anesthesia_codes())

    logger.info("")
    logger.info("=" * 70)
    logger.info(f"Total codes generated: {len(all_codes):,}")
    logger.info("=" * 70)

    # Category breakdown
    category_counts = {}
    for code in all_codes:
        cat = code['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    logger.info("")
    logger.info("Category breakdown:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {cat}: {count:,} codes")

    if args.dry_run:
        logger.info("")
        logger.info("DRY RUN - No file written")
        logger.info("")
        logger.info("Sample codes (first 10):")
        for i, code in enumerate(all_codes[:10], 1):
            logger.info(f"  {i}. {code['code']:6} ({code['category']:12}) - {code['paraphrased_desc'][:60]}...")
        return 0

    # Write to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_csv(all_codes, output_path)

    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ Generation completed successfully!")
    logger.info("=" * 70)
    logger.info(f"Output file: {output_path}")
    logger.info(f"File size: {output_path.stat().st_size:,} bytes")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review the generated codes")
    logger.info("2. Load into database: python scripts/load_procedure_codes.py")
    logger.info("3. Generate embeddings: python scripts/generate_procedure_embeddings.py")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
