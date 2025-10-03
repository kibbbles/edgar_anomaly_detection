# SEC EDGAR Risk Factor Analysis - AI Project

## Project Overview
Proof-of-concept AI system analyzing 10-K Risk Factor disclosures (Item 1A) for 20 companies across 5 years (2020-2024).
Total scope: 100 filings, 80 year-over-year comparison pairs.

**Core Capabilities:**
- Extract Item 1A sections via SEC EDGAR API
- Detect YoY changes (new/removed/modified risks)
- Classify risk categories (operational, financial, legal, cyber, etc.)
- Score boilerplate vs. substantive disclosure
- Interactive dashboard for analysis

## Working Principles

### File Management
- **DELETE** one-off helper scripts immediately after use
- **CONFIRM** before creating any .py file (state purpose, scope, key functions)
- **CONFIRM** before creating new folders (explain structure rationale)
- Keep repository clean - only essential files committed

### Code Organization
- Notebooks (`notebooks/`) for experimentation only
- Production code lives in `src/` modules
- Move working notebook code to `src/` immediately
- No duplicate logic between notebooks and modules

### Version Control (Git)
- Commit after each working feature
- Meaningful commit messages: "Add SEC API client with rate limiting"
- `.gitignore`: exclude `data/raw/`, `data/processed/`, `.ipynb_checkpoints/`, `__pycache__/`, `.env`
- Branch strategy: `main` for stable code, feature branches for experiments
- Push to GitHub after major milestones

## Core Files (Keep These)

### Data Layer (`src/data/`)
- `edgar_client.py` - SEC API wrapper, handles rate limiting (10 req/sec), downloads filings
- `risk_extractor.py` - Extract Item 1A from HTML/XML/text, parse into structured format

### Model Layer (`src/models/`)
- `risk_comparator.py` - YoY semantic similarity using sentence-transformers
- `risk_classifier.py` - Categorize risks (operational/financial/legal/cyber)
- `boilerplate_scorer.py` - Score generic vs. specific language

### Pipeline Layer (`src/pipeline/`)
- `analysis_pipeline.py` - End-to-end orchestration: ticker → download → extract → analyze → report

### Dashboard (`dashboard/`)
- `streamlit_app.py` - Interactive UI for exploring risk analysis

## Utility Functions (Candidates for Deletion After Use)

### One-Off Scripts
- Data validation scripts after initial download
- Manual inspection helpers
- Format conversion utilities (unless reused frequently)
- Debugging/logging scripts for specific issues

**Rule:** If a script is used once and won't be needed again, DELETE it immediately.

## Technical Stack
- **Python 3.10+**
- **NLP:** sentence-transformers (all-mpnet-base-v2), transformers, scikit-learn
- **Data:** pandas, numpy, requests
- **Dashboard:** streamlit
- **Storage:** JSON/Parquet (no database initially)

## Data Scope
- **Companies:** 20 (diverse sectors)
- **Years:** 5 (FY 2020-2024)
- **Total Filings:** 100 10-Ks
- **Comparisons:** 80 YoY pairs

## SEC EDGAR API
- Base: `https://data.sec.gov/`
- User-Agent required: `"Your Name email@company.com"`
- Rate limit: 10 requests/second
- Submissions: `https://data.sec.gov/submissions/CIK{10-digit}.json`

## Success Metrics
- Extract Item 1A from 90%+ filings
- Detect YoY changes with 80%+ accuracy (manual validation on 10 samples)
- Dashboard loads results in <5 seconds

## Current Phase
**Phase 1: Data Collection (Weeks 1-2)**
- [ ] Set up project structure
- [ ] Implement `edgar_client.py`
- [ ] Download 100 10-Ks (20 companies × 5 years)
- [ ] Implement `risk_extractor.py`
- [ ] Validate Item 1A extraction on 10 sample filings
- [ ] Store in structured format (JSON/Parquet)

## Next Steps
1. Confirm project folder structure
2. Initialize Git repository
3. Create `edgar_client.py` (with confirmation)
4. Test on 3 companies before scaling to 20
5. Build extraction logic iteratively

## Notes
- SEC filings are inconsistently formatted - expect iteration on extraction
- Don't over-engineer - get end-to-end working first, optimize later
- Manual validation is critical before scaling
- Focus on Item 1A only - no scope creep to other 10-K sections

---
**Last Updated:** 2025-10-03
**Status:** Project initialization
