# SEC EDGAR Risk Factor Analysis

AI-powered analysis of 10-K Risk Factor disclosures (Item 1A) to detect year-over-year changes, classify risk types, and identify material disclosures.

## Project Scope
- **Companies:** 20 publicly traded companies
- **Time Period:** 5 fiscal years (2020-2024)
- **Total Filings:** 100 10-K reports
- **Analysis:** 80 year-over-year comparison pairs

## Features
- Extract Item 1A (Risk Factors) from SEC EDGAR filings
- Year-over-year change detection (new/removed/modified risks)
- Risk classification (operational, financial, legal, cybersecurity)
- Boilerplate vs. substantive disclosure scoring
- Automated analysis pipeline

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

### 3. Run Data Collection
```bash
python src/data/edgar_10k_scraper.py
```

This will download 100 10-K filings (20 companies × 5 years) to `data/raw/`.

## Project Structure
```
edgar_anomaly_detection/
├── README.md
├── CLAUDE.md                          # Development guidelines
├── requirements.txt
├── .gitignore
├── .env.example
│
├── config/
│   └── companies.json                 # 20 target companies (AAPL, MSFT, JPM, etc.)
│
├── notebooks/                         # Jupyter notebooks for exploration
│   └── (TBD)
│
├── src/                               # Production source code
│   ├── data/
│   │   ├── edgar_10k_scraper.py      # ✅ Download 10-K filings from SEC EDGAR
│   │   └── section_extractor.py       # (TBD) Extract Item 1A sections
│   │
│   ├── models/                        # NLP models
│   │   ├── risk_comparator.py         # (TBD) Year-over-year comparison
│   │   ├── risk_classifier.py         # (TBD) Risk categorization
│   │   └── boilerplate_scorer.py      # (TBD) Quality scoring
│   │
│   ├── pipeline/
│   │   └── analysis_pipeline.py       # (TBD) End-to-end orchestration
│   │
│   └── analysis/
│       └── report_generator.py        # (TBD) Output JSON/CSV reports
│
├── data/                              # Data storage (gitignored)
│   ├── raw/                           # Downloaded 10-K HTML files
│   ├── processed/                     # Extracted Item 1A data
│   └── reports/                       # Analysis outputs
│
└── tests/
    └── test_edgar_10k_scraper.py     # (TBD)
```

## Current Files

### ✅ Completed
- **`edgar_10k_scraper.py`** - Downloads 10-K filings from SEC EDGAR API with rate limiting (10 req/sec)
- **`companies.json`** - 20 companies across diverse sectors (tech, finance, healthcare, retail, energy)

### 📋 To Do
- Section extraction (Item 1A)
- NLP models for YoY comparison
- Risk classification
- Analysis pipeline

## Usage
```python
from src.data.edgar_10k_scraper import Edgar10KScraper

# Download filings for all configured companies
scraper = Edgar10KScraper()
scraper.download_all_companies(
    companies_json_path="config/companies.json",
    years=[2020, 2021, 2022, 2023, 2024]
)
```

See `notebooks/` for data exploration examples (coming soon).

## Technical Stack
- **Python 3.10+**
- **NLP:** sentence-transformers, transformers, scikit-learn
- **Data:** pandas, numpy, requests
- **Storage:** JSON/Parquet
- **SEC EDGAR API** (data source)

## Status
**Phase 1: Data Collection** - In Progress
- [x] Project setup
- [x] SEC EDGAR scraper implemented
- [x] Download 118 10-K filings (20 companies × 5-6 years each)
- [ ] Item 1A extraction
- [ ] Data validation

## Recent Progress
- ✅ Successfully downloaded 118 10-K filings from SEC EDGAR
- ✅ Created `.env` configuration for SEC API access
- ✅ Verified all 20 companies have filings downloaded (stored in `data/raw/`)
