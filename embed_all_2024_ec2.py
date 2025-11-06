"""
Embed All 2024 SEC Filings - EC2 GPU Version

Generates embeddings for all 26,014 filings from processed_2024_500tok_contextual.json
and saves them in parquet format for RAG querying.

**EC2 PATHS:**
Input: /app/data/processed/2024_filings/processed_2024_500tok_contextual.json
Output: /app/data/embeddings/2024/

Model: multi-qa-mpnet-base-dot-v1 (768-dim, optimized for Q&A)
Device: CUDA GPU (automatic detection)

Usage (inside Docker):
    python /app/embed_all_2024_ec2.py
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch

# Configuration - EC2 PATHS
INPUT_FILE = Path('/app/data/processed/2024_filings/processed_2024_500tok_contextual.json')
OUTPUT_DIR = Path('/app/data/embeddings/2024')
MODEL_NAME = 'sentence-transformers/multi-qa-mpnet-base-dot-v1'
BATCH_SIZE = 128  # Increased for GPU

print("=" * 80)
print("EMBED ALL 2024 SEC FILINGS - EC2 GPU VERSION")
print("=" * 80)

# Check GPU availability
print(f"\n[GPU CHECK]")
print(f"  CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("  WARNING: No GPU detected, will use CPU (slow!)")

# Step 1: Load processed filings
print(f"\n[1/4] Loading processed filings from {INPUT_FILE}...")
if not INPUT_FILE.exists():
    print(f"[ERROR] Input file not found: {INPUT_FILE}")
    sys.exit(1)

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    filings = json.load(f)

print(f"[OK] Loaded {len(filings):,} filings")

# Step 2: Extract chunks for embedding
print(f"\n[2/4] Extracting chunks...")
texts_for_embedding = []
texts_for_retrieval = []
metadata_list = []

for filing in tqdm(filings, desc="Processing filings"):
    file_name = filing['file_name']

    for chunk in filing['chunks']:
        # Text to embed (extended with context)
        texts_for_embedding.append(chunk['text_for_embedding'])

        # Text to store for retrieval (core chunk)
        texts_for_retrieval.append(chunk['text'])

        # Metadata
        metadata = {
            'file_name': file_name,
            'chunk_id': chunk['chunk_id'],
            'company': chunk['metadata']['company'],
            'form_type': chunk['metadata']['form_type'],
            'filing_date': chunk['metadata']['filing_date'],
            'cik': chunk['metadata']['cik'],
            'chunk_index': chunk['metadata']['chunk_index'],
            'core_tokens': chunk['metadata']['core_tokens']
        }
        metadata_list.append(metadata)

total_chunks = len(texts_for_embedding)
print(f"\n[OK] Extracted {total_chunks:,} chunks")
print(f"  Avg chunks per filing: {total_chunks / len(filings):.1f}")

# Step 3: Generate embeddings
print(f"\n[3/4] Generating embeddings...")
print(f"  Model: {MODEL_NAME}")
print(f"  Batch size: {BATCH_SIZE}")
if torch.cuda.is_available():
    print(f"  Using GPU - Expected time: 30-60 minutes")
else:
    print(f"  Using CPU - Expected time: 8-10 hours")
print()

# Load model
print(f"[INFO] Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)
print(f"[OK] Model loaded")
print(f"  Dimensions: {model.get_sentence_embedding_dimension()}")
print(f"  Max sequence length: {model.max_seq_length}")
print(f"  Device: {model.device}\n")

# Generate embeddings with progress bar
embeddings = model.encode(
    texts_for_embedding,
    batch_size=BATCH_SIZE,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True,  # Important for dot-product similarity
    device=None  # Auto-detect GPU
)

print(f"\n[OK] Embeddings generated")
print(f"  Shape: {embeddings.shape}")
print(f"  Expected: ({total_chunks:,}, 768)")

# Validation
assert embeddings.shape[0] == total_chunks, "Mismatch in embedding count!"
assert embeddings.shape[1] == 768, "Incorrect embedding dimensions!"
assert not np.isnan(embeddings).any(), "NaN values found!"
assert not np.isinf(embeddings).any(), "Inf values found!"

norms = np.linalg.norm(embeddings, axis=1)
assert np.allclose(norms, 1.0, atol=1e-6), "Embeddings not normalized!"

print(f"[OK] Validation passed")
print(f"  L2 norm: {norms.mean():.6f} (should be ~1.0)")

# Step 4: Save embeddings and metadata
print(f"\n[4/4] Saving to {OUTPUT_DIR}...")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Save embeddings as parquet
embeddings_df = pd.DataFrame(embeddings)
embeddings_path = OUTPUT_DIR / 'embeddings.parquet'
embeddings_df.to_parquet(embeddings_path, index=False)

embeddings_size_mb = embeddings_path.stat().st_size / (1024 * 1024)
print(f"[OK] Embeddings saved: {embeddings_path.name}")
print(f"  Size: {embeddings_size_mb:,.2f} MB")

# Save metadata as parquet
metadata_df = pd.DataFrame(metadata_list)
metadata_path = OUTPUT_DIR / 'metadata.parquet'
metadata_df.to_parquet(metadata_path, index=False)

metadata_size_mb = metadata_path.stat().st_size / (1024 * 1024)
print(f"[OK] Metadata saved: {metadata_path.name}")
print(f"  Size: {metadata_size_mb:,.2f} MB")

# Save retrieval texts as parquet (for RAG queries)
retrieval_df = pd.DataFrame({'text': texts_for_retrieval})
retrieval_path = OUTPUT_DIR / 'retrieval_texts.parquet'
retrieval_df.to_parquet(retrieval_path, index=False)

retrieval_size_mb = retrieval_path.stat().st_size / (1024 * 1024)
print(f"[OK] Retrieval texts saved: {retrieval_path.name}")
print(f"  Size: {retrieval_size_mb:,.2f} MB")

# Summary
print("\n" + "=" * 80)
print("EMBEDDING COMPLETE")
print("=" * 80)

print(f"\nStatistics:")
print(f"  Total filings: {len(filings):,}")
print(f"  Total chunks: {total_chunks:,}")
print(f"  Embedding dimensions: 768")
print(f"  Total size: {embeddings_size_mb + metadata_size_mb + retrieval_size_mb:,.2f} MB")
print(f"  Device used: {model.device}")

print(f"\nOutput files:")
print(f"  {OUTPUT_DIR / 'embeddings.parquet'}")
print(f"  {OUTPUT_DIR / 'metadata.parquet'}")
print(f"  {OUTPUT_DIR / 'retrieval_texts.parquet'}")

print(f"\nNext steps:")
print(f"  1. Test RAG queries with: python -m src.pipeline.rag_query --embeddings /app/data/embeddings/2024")
print(f"  2. Run ground truth evaluation")
print(f"  3. Compare with baseline results")

print("\n" + "=" * 80)
