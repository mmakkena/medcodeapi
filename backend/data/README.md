# Procedure Code Data Files

This directory contains procedure code data files that are bundled with the Docker image for reliable, fast deployments.

## 📁 Directory Structure

```
data/
└── procedure_codes/
    ├── cpt_2025_sample.csv      # Sample CPT codes (151 codes)
    └── hcpcs_2025_sample.csv    # Sample HCPCS codes (16 codes)
```

## 📊 Data Files

### CPT 2025 Sample (`cpt_2025_sample.csv`)

**Total Codes**: 151 commonly used CPT codes
**License Status**: `free` (paraphrased descriptions, no AMA license)
**Version Year**: 2025

**Coverage:**
- **E/M Codes** (40 codes): Office visits, hospital care, ER visits, preventive medicine
- **Surgery** (35 codes): Minor procedures, arthroscopy, endoscopy
- **Radiology** (45 codes): X-rays, CT, MRI, ultrasound, mammography
- **Laboratory** (20 codes): Blood tests, cultures, panels
- **Medicine** (11 codes): Vaccines, ECG, injections, physical therapy

**Note**: These are paraphrased descriptions to avoid AMA copyright. For official CPT descriptions, an AMA license is required.

### HCPCS 2025 Sample (`hcpcs_2025_sample.csv`)

**Total Codes**: 16 commonly used HCPCS Level II codes
**License Status**: `free` (public domain)
**Version Year**: 2025

**Coverage:**
- **Drugs** (J codes): Botox, insulin, injections
- **Equipment** (E codes): Hospital beds, oxygen equipment, CPAP
- **Supplies** (A codes): Test strips, sterile water, infusion supplies
- **Services** (G/S codes): Annual wellness visits, home infusion

---

## 🔄 Loading Data

### Automatic Loading (Production)

Data is automatically loaded during container startup if tables are empty:

```bash
# In Dockerfile CMD
alembic upgrade head && python scripts/load_procedure_codes.py && uvicorn app.main:app
```

### Manual Loading (Development)

```bash
# Load procedure codes
python backend/scripts/load_procedure_codes.py

# Generate embeddings
python backend/scripts/generate_procedure_embeddings.py

# Populate facets
python backend/scripts/populate_procedure_facets.py
```

---

## 📝 CSV Format

Both files follow the same CSV structure:

```csv
code,code_system,paraphrased_desc,short_desc,category,license_status,version_year
99213,CPT,Established patient office visit - low to moderate complexity,,E/M,free,2025
J0585,HCPCS,Botulinum toxin type A injection,Injection botulinum toxin type A per unit,Drugs,free,2025
```

**Fields:**
- `code`: Procedure code (e.g., "99213", "J0585")
- `code_system`: "CPT" or "HCPCS"
- `paraphrased_desc`: Free paraphrased description (always included)
- `short_desc`: Official description (only for HCPCS, empty for CPT without license)
- `category`: Code category (E/M, Surgery, Radiology, etc.)
- `license_status`: "free" or "AMA_licensed"
- `version_year`: CPT/HCPCS version year (2025)

---

## 🔒 License Compliance

### CPT Codes
- **Owner**: American Medical Association (AMA)
- **License**: Proprietary - requires AMA license for official descriptions
- **Our Approach**: Use paraphrased descriptions (free tier)
- **Compliance**: Code numbers are not copyrighted; descriptions are
- **Note**: Include AMA copyright notice in API responses

### HCPCS Codes
- **Owner**: Centers for Medicare & Medicaid Services (CMS)
- **License**: Public domain
- **Our Approach**: Use official CMS descriptions
- **Compliance**: Full text usage allowed

---

## 🚀 Expanding the Dataset

To add more codes:

1. **Add to CSV files**: Edit `cpt_2025_sample.csv` or `hcpcs_2025_sample.csv`
2. **Rebuild Docker image**: Data is copied into image during build
3. **Re-run loader**: `python scripts/load_procedure_codes.py`
4. **Generate embeddings**: `python scripts/generate_procedure_embeddings.py`
5. **Populate facets**: `python scripts/populate_procedure_facets.py`

### Future: Licensed CPT Data

If you obtain an AMA CPT license:

1. Download official CPT data file
2. Add as `cpt_2025_licensed.csv`
3. Set `license_status=AMA_licensed`
4. Include `short_desc` and `long_desc` from AMA data
5. Update loader to process licensed data

---

## 📈 Data Statistics

| Dataset | Codes | Categories | License |
|---------|-------|------------|---------|
| CPT 2025 | 151 | 5 (E/M, Surgery, Radiology, Lab, Medicine) | Free (Paraphrased) |
| HCPCS 2025 | 16 | 4 (Drugs, Equipment, Supplies, Services) | Free (Public Domain) |
| **Total** | **167** | **9** | **Free** |

---

## 🎯 Coverage Analysis

### Most Common Use Cases Covered

✅ Office visits (new and established patients)
✅ Hospital and emergency care
✅ Preventive medicine / annual wellness
✅ Common lab tests (CBC, CMP, glucose, lipids)
✅ Basic imaging (X-ray, ultrasound)
✅ Advanced imaging (CT, MRI)
✅ Common vaccines (flu, COVID, pneumococcal)
✅ Minor surgical procedures
✅ Diagnostic procedures (endoscopy, colonoscopy)
✅ Therapeutic injections
✅ Durable medical equipment

### Not Yet Covered (Future Expansion)

❌ Specialized surgical procedures
❌ Complex interventional radiology
❌ Genetic testing codes
❌ Advanced pathology
❌ Rare disease treatments
❌ Experimental procedures

---

## 📞 Data Sources

- **HCPCS**: https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system
- **CPT Information**: https://www.ama-assn.org/practice-management/cpt
- **Paraphrased Descriptions**: Created by medical coding experts

---

## ⚠️ Disclaimer

This dataset is provided for development and demonstration purposes. For production use in billing and clinical documentation:

1. **Verify codes** with current CPT/HCPCS references
2. **Check effective dates** for the appropriate billing period
3. **Consult coding guidelines** for proper code selection
4. **Obtain proper licenses** if using official CPT descriptions
5. **Validate compliance** with payer-specific requirements

**Not for clinical diagnosis or treatment decisions.**
