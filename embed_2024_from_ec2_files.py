"""
Embed All 2024 SEC Filings - Using Existing EC2 Files

Reads from existing processed JSON files on EC2 and generates embeddings.

Input: /app/data/processed/2024/QTR*/*.json (26,000 individual files)
Output: /app/data/embeddings/2024/ (parquet files)

Model: multi-qa-mpnet-base-dot-v1 (768-dim)
Device: CUDA GPU (automatic detection)

Usage:
    python /app/embed_2024_from_ec2_files.py
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch
import glob

# Configuration
PROCESSED_DIR = Path('/app/data/processed/2024')
OUTPUT_DIR = Path('/app/data/embeddings/2024')
MODEL_NAME = 'sentence-transformers/multi-qa-mpnet-base-dot-v1'
BATCH_SIZE = 128  # For GPU

print("=" * 80)
print("EMBED ALL 2024 SEC FILINGS - FROM EXISTING EC2 FILES")
print("=" * 80)

# Check GPU
print(f"\n[GPU CHECK]")
print(f"  CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("  WARNING: No GPU detected, will use CPU (slower)")

# Step 1: Find all JSON files
print(f"\n[1/4] Finding JSON files in {PROCESSED_DIR}...")
json_files = []
for qtr in ['QTR1', 'QTR2', 'QTR3', 'QTR4']:
    qtr_path = PROCESSED_DIR / qtr
    if qtr_path.exists():
        files = list(qtr_path.glob('*.json'))
        json_files.extend(files)
        print(f"  {qtr}: {len(files):,} files")

print(f"\n[OK] Found {len(json_files):,} JSON files")

# Step 2: Load and extract chunks
print(f"\n[2/4] Loading chunks from JSON files...")
texts_for_embedding = []
texts_for_retrieval = []
metadata_list = []

for json_file in tqdm(json_files, desc="Loading files"):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            filing = json.load(f)

        # Get metadata from top level
        file_metadata = filing.get('metadata', {})
        file_name = file_metadata.get('filename', json_file.name)

        for chunk in filing.get('chunks', []):
            # Text to embed and retrieve (same, since context_summary is None)
            chunk_text = chunk['text']
            texts_for_embedding.append(chunk_text)
            texts_for_retrieval.append(chunk_text)

            # Metadata
            metadata = {
                'file_name': file_name,
                'chunk_id': chunk['chunk_id'],
                'company': file_metadata.get('company_name', 'Unknown'),
                'form_type': file_metadata.get('form_type', 'Unknown'),
                'filing_date': file_metadata.get('filing_date', 'Unknown'),
                'cik': file_metadata.get('cik', 'Unknown'),
                'chunk_index': chunk['chunk_id'],
                'core_tokens': chunk.get('token_count', 0)
            }
            metadata_list.append(metadata)

    except Exception as e:
        print(f"\n[WARN] Failed to load {json_file.name}: {e}")
        continue

total_chunks = len(texts_for_embedding)
print(f"\n[OK] Extracted {total_chunks:,} chunks from {len(json_files):,} filings")
print(f"  Avg chunks per filing: {total_chunks / len(json_files):.1f}")

# Step 3: Generate embeddings
print(f"\n[3/4] Generating embeddings...")
print(f"  Model: {MODEL_NAME}")
print(f"  Batch size: {BATCH_SIZE}")
if torch.cuda.is_available():
    print(f"  Using GPU - Expected time: 30-60 minutes")
else:
    print(f"  Using CPU - Expected time: 2-3 hours")
print()

# Load model
print(f"[INFO] Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)
print(f"[OK] Model loaded")
print(f"  Dimensions: {model.get_sentence_embedding_dimension()}")
print(f"  Max sequence length: {model.max_seq_length}")
print(f"  Device: {model.device}\n")

# Generate embeddings
embeddings = model.encode(
    texts_for_embedding,
    batch_size=BATCH_SIZE,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True,
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

# Save embeddings
embeddings_df = pd.DataFrame(embeddings)
embeddings_path = OUTPUT_DIR / 'embeddings.parquet'
embeddings_df.to_parquet(embeddings_path, index=False)
embeddings_size_mb = embeddings_path.stat().st_size / (1024 * 1024)
print(f"[OK] Embeddings saved: {embeddings_path.name} ({embeddings_size_mb:,.2f} MB)")

# Save metadata
metadata_df = pd.DataFrame(metadata_list)
metadata_path = OUTPUT_DIR / 'metadata.parquet'
metadata_df.to_parquet(metadata_path, index=False)
metadata_size_mb = metadata_path.stat().st_size / (1024 * 1024)
print(f"[OK] Metadata saved: {metadata_path.name} ({metadata_size_mb:,.2f} MB)")

# Save retrieval texts
retrieval_df = pd.DataFrame({'text': texts_for_retrieval})
retrieval_path = OUTPUT_DIR / 'retrieval_texts.parquet'
retrieval_df.to_parquet(retrieval_path, index=False)
retrieval_size_mb = retrieval_path.stat().st_size / (1024 * 1024)
print(f"[OK] Retrieval texts saved: {retrieval_path.name} ({retrieval_size_mb:,.2f} MB)")

# Summary
print("\n" + "=" * 80)
print("EMBEDDING COMPLETE")
print("=" * 80)

print(f"\nStatistics:")
print(f"  Total filings: {len(json_files):,}")
print(f"  Total chunks: {total_chunks:,}")
print(f"  Embedding dimensions: 768")
print(f"  Total size: {embeddings_size_mb + metadata_size_mb + retrieval_size_mb:,.2f} MB")
print(f"  Device used: {model.device}")

print(f"\nOutput files:")
print(f"  {OUTPUT_DIR / 'embeddings.parquet'}")
print(f"  {OUTPUT_DIR / 'metadata.parquet'}")
print(f"  {OUTPUT_DIR / 'retrieval_texts.parquet'}")

print(f"\nNext steps:")
print(f"  1. Test RAG: python -m src.pipeline.rag_query --embeddings /app/data/embeddings/2024")
print(f"  2. Run ground truth evaluation")

print("\n" + "=" * 80)
