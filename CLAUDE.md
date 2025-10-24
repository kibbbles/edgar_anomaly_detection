# SEC EDGAR 10-K/10-Q Analysis - RAPTOR RAG System

## Project Overview
AI-powered system analyzing complete SEC 10-K and 10-Q filings (1993-2024) using RAPTOR RAG (Recursive Adaptive Processing and Topical Organizational Retrieval).

**Data Coverage:** 31 years of SEC EDGAR filings (~51 GB)

**Core Capabilities:**
- Process entire 10-K/10-Q filings (all sections)
- Hierarchical clustering and multi-level summarization
- Interactive querying via Open WebUI
- Semantic search across full filing content
- Year-over-year analysis across any section

---

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

### Python Encoding Best Practices
- **ALWAYS** set `encoding='utf-8'` when opening files for reading/writing
- **AVOID** using emojis or special Unicode characters in print statements (Windows cp1252 encoding issues)
- **USE** ASCII-safe alternatives: `[OK]` instead of ✅, `[FAIL]` instead of ❌, `[WARN]` instead of ⚠️
- If Unicode is required, wrap print statements with encoding handling:
  ```python
  import sys
  sys.stdout.reconfigure(encoding='utf-8')  # At script start
  ```
- Common error to avoid: `UnicodeEncodeError: 'charmap' codec can't encode character`

### Version Control (Git)
- Commit after each working feature
- Meaningful commit messages: "Add RAPTOR clustering implementation"
- `.gitignore`: exclude `data/external/`, `data/processed/`, `.ipynb_checkpoints/`, `__pycache__/`, `.env`, `CLAUDE.md`, `resources/`
- Branch strategy: `master` for stable code, feature branches for experiments
- Push to GitHub after major milestones

---

## Core Files (Keep These)

### Data Layer (`src/data/`)
- `filing_extractor.py` - Unzip archives, extract full 10-K/10-Q text from HTML/XML/SGML
- `text_processor.py` - Clean text, chunk into 500-token segments with contextual chunking (100-token context prepended per chunk)

### Model Layer (`src/models/`)
- `raptor.py` - RAPTOR class (adapted from FinGPT): hierarchical clustering, recursive summarization
- `embedding_generator.py` - Generate embeddings using Sentence Transformers
- `clustering.py` - UMAP + GMM clustering implementation

### Pipeline Layer (`src/pipeline/`)
- `knowledge_base_builder.py` - End-to-end: extract → chunk → embed → cluster → summarize → store

### Dashboard (`dashboard/`)
- Open WebUI integration for interactive querying

---

## Utility Functions (Candidates for Deletion After Use)

### One-Off Scripts
- Data validation scripts after initial extraction
- Format inspection helpers
- Debugging/logging scripts for specific issues

**Rule:** If a script is used once and won't be needed again, DELETE it immediately.

---

## Technical Stack

### Core Technologies
- **Python 3.12** (inside Docker containers)
- **LLM Model:** qwen2.5:1.5b or llama3 (via Ollama, for contextual summary generation)
- **RAPTOR:** Adapted from FinGPT's `FinancialReportAnalysis/utils/rag.py`
- **Embeddings:** Sentence Transformers (`multi-qa-mpnet-base-dot-v1`, 768-dim)
- **Clustering:** UMAP + scikit-learn GMM
- **Vector Store:** ChromaDB
- **UI:** Open WebUI
- **Containerization:** Docker (all processing happens inside containers)

### Deployment Strategy
- **ALL packages and dependencies MUST be installed inside Docker containers**
- **NO manual pip installs on EC2 host** - keep the host clean
- **Reuse existing Docker image** (`edgar-chunking`) when possible
- Add new dependencies to `requirements.txt` → rebuild image → deploy

### Libraries
- `langchain`, `langchain_community` - LLM orchestration
- `sentence-transformers` - 768-dim embeddings (multi-qa-mpnet-base-dot-v1)
- `umap-learn` - Dimensionality reduction
- `scikit-learn` - Clustering algorithms
- `pandas`, `numpy` - Data manipulation
- `ollama` - LLM client for contextual summary generation
- `tiktoken` - Token counting for chunking
- `tqdm` - Progress bars
- `pyarrow` - Parquet file format support

---

## Data Scope

### Current Holdings
- **Time Period:** 1993-2024 (31 years)
- **Data Size:** ~51 GB in `data/external/`
- **Filing Types:** Complete 10-K and 10-Q filings (all sections)
- **Format:** ZIP archives organized by year ranges

### Processing Approach
- Extract **entire filings** (not limited to specific sections)
- **Contextual Chunking (Anthropic's Method):**
  - Core chunk: 500 tokens (stored for retrieval)
  - LLM-generated context: 50-100 tokens explaining chunk's role in document
  - Contextualized chunk: [context] + [core chunk] (embedded for search)
  - LLM: qwen2.5:1.5b via Ollama (fast, efficient)
  - Expected improvement: 35-49% better retrieval accuracy
- RAPTOR clustering will naturally organize content by topic
- Users can query any section or topic across all filings

---

## SEC EDGAR Data
- Data Source: Notre Dame SRAF 10-X Cleaned Files
- Format: HTML, XML, SGML (varies by time period)
- Coverage: 1993-2024

---

## Success Metrics
- Process 90%+ of filings (1993-2024) into knowledge base
- Clustering produces coherent, interpretable topic groups
- Generated summaries accurately capture content at each hierarchical level
- LLM queries return relevant responses in <10 seconds
- Manual validation: Test 10 YoY comparison queries, verify accuracy

---

## Implementation Phases

### Phase 1: Model Research & Setup ✅
- [x] Clarify FinGPT components (model vs. implementation)
- [ ] Pull FinGPT-v3 into Ollama
- [ ] Copy RAPTOR class from FinGPT's `rag.py`
- [ ] Set up project structure

### Phase 2: Data Processing Pipeline
- [ ] Extract filings from ZIP archives (1993-2024)
- [ ] Parse full 10-K/10-Q text (handle HTML/XML/SGML)
- [ ] Chunk documents (500 tokens/chunk + 100-token contextual summary prepended)
- [ ] Generate embeddings
- [ ] Store structured data (JSON/Parquet)

### Phase 3: RAPTOR Implementation
- [ ] Implement hierarchical clustering (UMAP + GMM)
- [ ] Build recursive summarization (3 levels)
- [ ] Create enhanced knowledge base
- [ ] Test on sample filings

### Phase 4: Deployment
- [ ] Set up Ollama on EC2 with FinGPT-v3
- [ ] Deploy Open WebUI
- [ ] Integrate RAPTOR with LLM
- [ ] Create query templates

---

## Next Steps
1. Extract sample filings to examine format evolution (1993 vs 2024)
2. Build `filing_extractor.py` to handle multiple formats
3. Test chunking strategy on diverse filings
4. Copy RAPTOR class to `src/models/raptor.py`

---

## Notes
- SEC filing formats evolved significantly (1993-2024): SGML → HTML → XML
- Process **entire filings** to maximize RAG system value
- Don't over-engineer - get end-to-end working first, optimize later
- Manual validation is critical before scaling to full dataset
- RAPTOR clustering handles content organization - no need to pre-filter sections

---

**Last Updated:** 2025-10-08
**Status:** Phase 1 (Model clarification complete) → Starting Phase 2 (Data processing)
