# SEC EDGAR Fraud Detection - 10-K/10-Q Analysis

AI-powered fraud detection system analyzing SEC EDGAR filings to identify anomalies in 10-K Risk Factors (Item 1A) and quarterly disclosures.

## Project Scope
- **Companies:** 23 (20 clean baseline + 3 known fraud cases)
- **Time Period:** 30+ years (1993-2024) via SRAF dataset
- **Primary Data Source:** Notre Dame SRAF 10-X Cleaned Files (1993-2024)
- **Supplementary Data:** Self-scraped 8-K filings (3,964 filings, 2015-2024)
- **Fraud Cases:** Under Armour, Nikola Corporation (Luckin Coffee - insufficient data)

## Objective
Build a machine learning model to detect early warning signs of corporate fraud by analyzing:
1. **10-K Item 1A (Risk Factors):** Year-over-year changes, boilerplate vs. substantive disclosures
2. **10-Q Quarterly Filings:** Trend analysis, MD&A changes
3. **Optional 8-K Analysis:** Event-driven anomalies (if time permits)

## Features
- Extract Item 1A from 10-K filings (SRAF cleaned text format)
- YoY risk factor change detection using NLP (semantic similarity)
- Boilerplate vs. substantive disclosure scoring
- Quarterly trend analysis from 10-Q filings
- Interactive dashboard for analysis
- Validation on known fraud cases (Under Armour 2015-2017, Nikola 2019-2020)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure SEC API Access
Create a `.env` file with your SEC API user agent:
```
SEC_USER_AGENT=YourName your.email@company.com
```

### 3. Data Collection

**Primary Source: Notre Dame SRAF Dataset**
1. Download 10-X cleaned files from https://sraf.nd.edu/sec-edgar-data/
2. Extract to `data/external/sraf/`
3. Files organized by year/quarter: `YYYY/QTRX/YYYYMMDD_FORM_*.txt`

**Supplementary Data (Optional):**
```bash
# Self-scraped 8-K filings (if needed for event analysis)
python src/data/edgar_8k_scraper.py
```

**Current Data Status:**
- ✅ SRAF 2016-2020: Downloaded (7.8 GB)
- 🔄 SRAF 2006-2015: Downloading
- 🔄 SRAF 2021-2024: Downloading
- ✅ Self-scraped 8-K (2015-2024): 3,964 filings in `data/raw/sec-edgar-filings/`
- ✅ Self-scraped 10-K (2015-2024): 230 filings in `data/raw/sec-edgar-filings/` (backup)

## Project Structure
```
edgar_anomaly_detection/
├── README.md
├── CLAUDE.md                          # Development guidelines
├── requirements.txt
├── .gitignore
├── .env
│
├── config/
│   └── companies.json                 # 23 companies (including fraud cases)
│
├── notebooks/
│   └── 01_data_collection_summary.ipynb  # ✅ Technical documentation
│
├── src/
│   ├── data/
│   │   ├── edgar_10k_scraper.py       # ✅ Download 10-K filings
│   │   ├── edgar_8k_scraper.py        # ✅ Download 8-K filings
│   │   ├── risk_extractor.py          # (TBD) Extract Item 1A sections
│   │   └── item_8k_extractor.py       # (TBD) Extract 8-K Items 4.02, 5.02, 8.01
│   │
│   ├── models/
│   │   ├── risk_comparator.py         # (TBD) YoY risk factor comparison
│   │   ├── risk_classifier.py         # (TBD) Risk categorization
│   │   └── fraud_detector.py          # (TBD) 8-K anomaly scoring
│   │
│   ├── pipeline/
│   │   └── analysis_pipeline.py       # (TBD) End-to-end orchestration
│   │
│   └── analysis/
│       └── report_generator.py        # (TBD) Generate fraud reports
│
├── dashboard/
│   └── streamlit_app.py               # (TBD) Interactive UI
│
├── data/                              # Excluded from Git
│   ├── raw/                           # Self-scraped filings (backup/supplement)
│   │   └── sec-edgar-filings/         # 4,194 filings: 230 × 10-K, 3,964 × 8-K
│   ├── external/                      # External datasets
│   │   └── sraf/                      # Notre Dame 10-X files (PRIMARY SOURCE)
│   │       ├── 10-X_C_2006-2015.zip
│   │       ├── 10-X_C_2016-2020.zip   # ✅ Downloaded
│   │       ├── 10-X_C_2021.zip
│   │       ├── 10-X_C_2022.zip
│   │       ├── 10-X_C_2023.zip
│   │       └── 10-X_C_2024.zip
│   ├── processed/                     # Extracted Item 1A sections
│   └── reports/                       # Analysis outputs
│
└── tests/
    └── (TBD)
```

## Current Status

### ✅ Completed (Week 1)
- [x] Project setup
- [x] Company selection (23 companies, 3 fraud cases)
- [x] 10-K scraper implemented (`edgar_10k_scraper.py`)
- [x] 8-K scraper implemented (`edgar_8k_scraper.py`)
- [x] Downloaded **230 × 10-K filings** (2015-2024)
- [x] Downloaded **3,964 × 8-K filings** (2015-2024)
- [x] Validated fraud case coverage
- [x] Documentation notebook created

### 📋 To-Do (Week 2-4)

**Week 2: Text Extraction**
- [ ] Build 10-K Item 1A extractor
- [ ] Build 8-K Item extractor (4.02, 5.02, 8.01, 2.01)
- [ ] Validate extraction on 10 sample filings
- [ ] Store extracted text in `data/processed/`

**Week 3: Feature Engineering**
- [ ] YoY risk factor change detection (semantic similarity)
- [ ] Boilerplate vs. substantive scoring
- [ ] 8-K anomaly features (frequency, clustering, sentiment)

**Week 4: Modeling & Dashboard**
- [ ] Train fraud detection model
- [ ] Validate on UAA, NKLA, LK
- [ ] Build Streamlit dashboard

## Download Summary

### 10-K Filings (Annual Reports)
- **Total:** 230 filings
- **Coverage:** 23 companies × ~10 years each
- **Fraud Cases:**
  - Under Armour (UAA): 11 filings
  - Nikola (NKLA): 6 filings
  - Luckin Coffee (LK): 0 filings (delisted)

### 8-K Filings (Event Disclosures)
- **Total:** 3,964 filings
- **Coverage:** 2015-2024
- **Fraud Cases:**
  - Under Armour (UAA): 141 filings
  - Nikola (NKLA): 118 filings
  - Luckin Coffee (LK): 0 filings (delisted)
- **Highest Volume:** Wells Fargo (869 filings - 2016 scandal)

## Fraud Cases

### 1. Under Armour (UAA)
- **Fraud Period:** 2015-2017
- **Type:** Accounting fraud (revenue manipulation via "pull-forward" sales)
- **SEC Settlement:** 2021 ($9M penalty)
- **Coverage:** ✅ 11 × 10-K, 141 × 8-K

### 2. Luckin Coffee (LK)
- **Fraud Period:** 2019-2020
- **Type:** Accounting fraud (fabricated sales ~$300M)
- **Exposed:** April 2020
- **Coverage:** ❌ 0 filings (delisted before 2015, not in SEC database)

### 3. Nikola Corporation (NKLA)
- **Fraud Period:** 2019-2020
- **Type:** Securities fraud (false product claims, Trevor Milton)
- **Exposed:** September 2020
- **Coverage:** ✅ 6 × 10-K, 118 × 8-K

## Usage

### Download Filings
```python
from src.data.edgar_10k_scraper import Edgar10KScraper
from src.data.edgar_8k_scraper import Edgar8KScraper

# Download 10-K filings
scraper_10k = Edgar10KScraper()
scraper_10k.download_all_companies(
    companies_json_path="config/companies.json",
    years=[2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
)

# Download 8-K filings
scraper_8k = Edgar8KScraper()
scraper_8k.download_all_companies(
    companies_json_path="config/companies.json",
    years=[2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
)
```

### Explore Data
See `notebooks/01_data_collection_summary.ipynb` for detailed analysis.

## File Structure (Downloaded Data)
```
data/raw/sec-edgar-filings/
├── {CIK}/                          # e.g., 0001336917 (Under Armour)
│   ├── 10-K/
│   │   └── {ACCESSION}/            # e.g., 0001336917-17-000032
│   │       ├── full-submission.txt # Complete filing
│   │       └── primary-document.html
│   └── 8-K/
│       └── {ACCESSION}/
│           ├── full-submission.txt
│           └── primary-document.html
```

## Technical Stack
- **Python 3.10+**
- **Data Collection:** `sec-edgar-downloader` (rate limiting, SEC API wrapper)
- **NLP:** `sentence-transformers`, `transformers`, `scikit-learn`
- **Data Processing:** `pandas`, `numpy`
- **Dashboard:** `streamlit`
- **Storage:** JSON, Parquet

## External Datasets Evaluation

**Evaluated 4 datasets** (see `external_datasets_evaluation.xlsx` for full analysis):

1. **✅ Notre Dame SRAF 10-X Files (PRIMARY SOURCE)**
   - Full 10-K/10-Q text (1993-2024)
   - Has Item 1A Risk Factors text
   - Cleaned .txt format, organized by year/quarter
   - **Decision:** Use as primary source for 10-K/10-Q analysis

2. **❌ Kaggle - SEC EDGAR Company Facts (Lang)**
   - 13.86 GB of structured XBRL financial line items only
   - No narrative text sections
   - **Decision:** Skip

3. **❌ Kaggle - Parsed 10-Q Filings (Aenlle)**
   - Quarterly financial metrics only
   - **Decision:** Skip

4. **❌ Kaggle - Company Facts v2 (Vanak)**
   - 75.4M rows of numerical metrics
   - **Decision:** Skip

**Key Finding:** All Kaggle datasets contain only structured financial numbers (XBRL). SRAF dataset is the only source with full filing text needed for NLP fraud detection.

## References
- **SEC EDGAR API:** https://www.sec.gov/edgar/sec-api-documentation
- **Under Armour SEC Charges:** https://www.sec.gov/newsroom/press-releases/2021-78
- **Luckin Coffee Settlement:** https://www.sec.gov/newsroom/press-releases/2020-319
- **Nikola/Trevor Milton Indictment:** https://www.sec.gov/newsroom/press-releases/2021-141

---

**Last Updated:** October 7, 2025
**Status:** Phase 1 Complete (Data Collection & Evaluation) → Phase 2 Starting (SRAF Download & Text Extraction)

**Recent Updates:**
- Evaluated 4 external datasets (3 Kaggle + 1 SRAF)
- Selected Notre Dame SRAF as primary source for 10-K/10-Q text
- Downloading SRAF files: 2006-2015, 2021-2024 (2016-2020 complete)
- Updated project scope: Focus on 10-K/10-Q, keep 8-K as supplementary
