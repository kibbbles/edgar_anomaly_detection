# Chunking Strategy Guide

## Why Chunk Size Matters

Chunk size is one of the most critical hyperparameters in RAG systems. It directly impacts:

### 1. Retrieval Quality
- **Too small (< 500 tokens):** Fragments information, loses context
- **Too large (> 8K tokens):** Includes too much irrelevant content, reduces precision
- **Just right (2K-4K for financial docs):** Balances context with precision

### 2. Embedding Model Constraints
Different models have different context limits:

| Model | Max Tokens | Best Use Case |
|-------|-----------|--------------|
| all-MiniLM-L6-v2 | 512 | Fast, but limited context |
| BGE-large-en-v1.5 | 512 | High quality, limited context |
| nomic-embed-text-v1.5 | 8192 | Long documents (our best bet) |
| jina-embeddings-v3 | 8192 | Multi-lingual, long context |

**Key insight:** If chunks exceed model limits, they get **truncated**, losing information!

### 3. LLM Context Window Usage
When answering a query, the RAG system retrieves multiple chunks:

**Example scenario:**
- Query: "What cyber risks did companies disclose in 2023?"
- System retrieves top 5 most relevant chunks

**With 2K chunks:**
- 5 chunks × 2K tokens = 10K tokens of context
- Leaves room for query, system prompt, and response (~20K tokens total)
- LLM sees focused, relevant information

**With 4K chunks:**
- 5 chunks × 4K tokens = 20K tokens of context
- Tighter fit, might need to retrieve fewer chunks (3-4)
- More context per chunk, but less diversity

### 4. Research-Backed Recommendations (2024)

**General documents:**
- Optimal: 512-1024 tokens
- Provides specific answers without excess context

**Financial documents (FinGPT research):**
- **Optimal: 500-1000 tokens** ⭐
- FinGPT was specifically trained and tested on SEC filings
- Smaller chunks work better for financial Q&A and fact extraction
- Financial metrics (revenue, earnings, etc.) are typically localized
- Don't need huge context to understand specific disclosures

**Long-form financial/legal documents (General RAG):**
- Optimal: 2000-4000 tokens
- Preserves narrative flow and complex relationships
- Better for understanding broad topics like entire risk factor sections

**Our comprehensive test plan:**
Test **12 different chunk sizes**: 200, 300, 400, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000, 8000 tokens

**Distribution rationale:**
- **200-500 tokens (5 sizes):** Dense coverage in FinGPT's optimal range for fact extraction
  - 200 tokens ≈ 150 words ≈ 2-3 paragraphs (minimum coherent size)
  - Why not smaller? 100-150 tokens fragments information too much
- **750-2000 tokens (3 sizes):** Standard RAG range for balanced context
  - 1000 tokens ≈ 750 words ≈ 1.5 pages
  - 2000 tokens ≈ 1500 words ≈ 3 pages
- **3000-5000 tokens (2 sizes):** Large context for narrative understanding
  - 3000 tokens ≈ 6 pages, 5000 tokens ≈ 10 pages
- **8000 tokens (1 size):** Stress test embedding model limits (nomic-embed max: 8192)
  - Tests if "more context = better" holds at extreme sizes
  - Likely too large (will include irrelevant content)

**Expected winner (based on FinGPT):** 500-1000 tokens for fact-based queries
- But we'll validate empirically with our specific queries and use cases
- Different query types may favor different chunk sizes:
  - Fact extraction: Likely 200-500 tokens
  - Narrative understanding: Likely 1000-2000 tokens
  - Complex reasoning: Possibly 2000-4000 tokens

## Overlap: Why and How Much?

### The Boundary Problem

Without overlap, sentences get split mid-thought:

```
[Chunk 1 ends]: "...gross margin improved due to operational effici-"
[Chunk 2 starts]: "-encies and reduced manufacturing costs in Q3..."
```

This breaks semantic meaning and hurts retrieval.

### Overlap Solution

With 10% overlap (200 tokens on 2K chunks):

```
[Chunk 1]: "...gross margin improved due to operational efficiencies
            and reduced manufacturing costs in Q3, driven by..."

[Chunk 2]: "...operational efficiencies and reduced manufacturing costs
            in Q3, driven by our new automation investments..."
```

### Recommended Overlap Sizes

**Rule of thumb: 10-20% of chunk size**

| Chunk Size | 10% Overlap | 20% Overlap | Recommendation |
|-----------|------------|------------|----------------|
| 2000 tokens | 200 tokens | 400 tokens | Use 200 (balanced) |
| 4000 tokens | 400 tokens | 800 tokens | Use 400 (balanced) |

**Why not more overlap?**
- Storage cost: More chunks = more embeddings to store
- Redundancy: Same information retrieved multiple times
- Diminishing returns: 20%+ overlap doesn't improve quality significantly

## How to Evaluate Chunk Size

### Method 1: Retrieval Quality (Most Important)

**Create test questions with known answers:**
```python
test_queries = [
    {
        "query": "What was Apple's revenue in Q3 2023?",
        "expected_answer": "$81.8 billion",
        "answer_location": "Apple 10-Q filed 2023-08-04"
    },
    {
        "query": "What cyber risks did Microsoft disclose in 2024?",
        "expected_answer": "Nation-state attacks, ransomware, supply chain...",
        "answer_location": "Microsoft 10-K filed 2024-07-30"
    }
]
```

**Evaluation metrics:**
1. **Retrieval precision:** Do top-5 chunks contain the answer? (0-100%)
2. **Answer accuracy:** Does LLM generate correct answer? (0-100%)
3. **Chunk rank:** What position is the best chunk? (1-5 = good, 6-10 = okay, 11+ = bad)
4. **Context quality:** How much irrelevant text is in retrieved chunks? (subjective 1-5 rating)

**Process:**
- Run same 20 test queries against all 10 chunk sizes
- Compare metrics across chunk sizes
- Best chunk size = highest precision + accuracy

### Method 2: Chunk Coherence (Qualitative)

**Manually inspect sample chunks:**
- Does each chunk make sense on its own?
- Are sentences cut off mid-thought?
- Does chunk contain a complete idea?

**Red flags:**
- Tables split across chunks (numbers separated from labels)
- List items separated from context
- "See section X" references without the referenced content

### Method 3: Coverage Analysis (Quantitative)

**Metrics to track:**
- Average chunks per filing (more chunks = finer granularity)
- Average tokens per chunk (check actual vs. target)
- Overlap effectiveness (how much content is duplicated)

**Example output:**
```
Chunk Size: 500 tokens
- Avg chunks/filing: 100
- Avg tokens/chunk: 487 (target: 500)
- Total chunks (1,375 files): 137,500
- Storage: ~200 MB embeddings

Chunk Size: 2000 tokens
- Avg chunks/filing: 28
- Avg tokens/chunk: 1,892 (target: 2000)
- Total chunks: 38,500
- Storage: ~55 MB embeddings
```

### Method 4: Speed & Storage (Practical)

**Processing time:**
- Smaller chunks = more chunks = longer processing
- 500 tokens: ~137K chunks to embed
- 2000 tokens: ~38K chunks to embed
- Embedding speed: ~100-500 chunks/second (depends on GPU)

**Storage requirements:**
- Each embedding: ~1536 dimensions × 4 bytes = 6 KB
- 500 tokens: 137K chunks × 6 KB = **~820 MB**
- 2000 tokens: 38K chunks × 6 KB = **~230 MB**

**Retrieval speed:**
- Smaller chunks = larger vector database = slower search
- But modern vector DBs (Qdrant, Weaviate) handle 100K+ vectors easily
- Speed difference negligible for our scale

## Time Estimates for Testing

### On 44 Sample Files (Fast Iteration)

**Processing time per chunk size:**
- Text extraction + chunking: ~2-5 seconds total (very fast)
- Embedding generation: ~30-60 seconds (depends on GPU)
- Total per chunk size: **~1 minute**

**Testing all 10 chunk sizes:** ~10-15 minutes

**Evaluation (manual review):** ~30-60 minutes
- Inspect sample chunks from each size
- Run test queries
- Compare results

**Total time on samples: ~1-2 hours** ✅ Very manageable!

### On Full Dataset (1,375 Files)

**Processing time per chunk size:**
- Text extraction + chunking: ~2-5 minutes
- Embedding generation: ~10-30 minutes (GPU) or ~1-2 hours (CPU)
- Total per chunk size: **~15-35 minutes (GPU)** or **~1-2 hours (CPU)**

**Testing all 10 chunk sizes:** ~3-6 hours (GPU) or ~10-20 hours (CPU)

**Recommendation:**
1. Test all 10 sizes on **44 samples** first (~1-2 hours)
2. Narrow down to top 3 chunk sizes based on sample results
3. Run full dataset on only top 3 candidates (~1-2 hours total)

This saves time while still being comprehensive!

## Our Testing Plan

### Phase 1: Comprehensive Chunk Size Testing (Current)
**Test 12 chunk sizes:** 200, 300, 400, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000, 8000 tokens

**Overlap strategy (10% of chunk size):**
- 200 tokens → 20 token overlap
- 300 tokens → 30 token overlap
- 400 tokens → 40 token overlap
- 500 tokens → 50 token overlap
- 750 tokens → 75 token overlap
- 1000 tokens → 100 token overlap
- 1500 tokens → 150 token overlap
- 2000 tokens → 200 token overlap
- 3000 tokens → 300 token overlap
- 4000 tokens → 400 token overlap
- 5000 tokens → 500 token overlap
- 8000 tokens → 800 token overlap

**Evaluation:**
- Run on 44 sample files first
- Use retrieval quality metrics (precision, accuracy, rank)
- Manual inspection of chunk coherence
- **Expected winner:** 500-1000 tokens for fact-based queries (FinGPT research)

### Phase 2: Overlap Optimization
- Take winning chunk size from Phase 1
- Test overlap: 0%, 5%, 10%, 15%, 20%
- Find optimal balance

### Phase 3: Semantic Chunking (Future)
- Chunk by section boundaries (e.g., "Risk Factors", "MD&A")
- Variable chunk sizes (500-5K based on section length)
- Compare to fixed-size baseline

### Phase 4: Hybrid Approach (Advanced)
- Small chunks (500-1K) for facts and figures
- Medium chunks (2K) for narrative sections
- RAPTOR hierarchical summaries on top

## Expected Results from Our Sample Data

From EDA findings:
- Average filing: ~50K tokens (35,904 words)
- With 2K chunks: ~25-28 chunks per filing
- With 4K chunks: ~12-14 chunks per filing

**44 sample files:**
- 2K chunking: ~1,200 total chunks
- 4K chunking: ~600 total chunks

**Full dataset (1,375 files from all years):**
- 2K chunking: ~38,000 total chunks (from notebook output)
- 4K chunking: ~19,000 total chunks (estimated)

## Next Steps

1. **Validate on samples** (current notebook)
   - Ensure chunks are semantically coherent
   - Check that metadata extraction works correctly

2. **Test retrieval quality** (next notebook: `02_chunking_strategies.ipynb`)
   - Create test queries like "What cyber risks were disclosed?"
   - Compare 2K vs 4K retrieval relevance

3. **Test embedding models** (`03_embedding_tests.ipynb`)
   - Test nomic-embed-text-v1.5 (8192 token limit)
   - Compare to BGE-large (512 token limit with chunking)

4. **Production implementation** (`src/prod/data/text_processor.py`)
   - Implement winning chunking strategy
   - Add error handling and logging
   - Optimize for batch processing

## References

- **Anthropic Contextual Retrieval (2024):** Add document context to each chunk
- **LangChain Chunking Guide:** Recommends 1K-4K for long documents
- **OpenAI Embeddings Best Practices:** 10-20% overlap optimal
- **Research (Liu et al. 2024):** Larger chunks (2K-4K) better for complex reasoning tasks
