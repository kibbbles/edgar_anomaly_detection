"""
Execute 03_embedding_generation.ipynb cells
Generate embeddings for all 2.7M contextually-chunked 2024 SEC filings
"""

import sys
from pathlib import Path
import json
import numpy as np
import time
from datetime import datetime

# Project root
project_root = Path.cwd().parent.parent
sys.path.insert(0, str(project_root))

# Paths
INPUT_FILE = project_root / 'notebooks' / 'prototyping' / 'output' / 'processed_2024_500tok_contextual.json'
OUTPUT_DIR = project_root / 'notebooks' / 'prototyping' / 'output'
OUTPUT_FILE = OUTPUT_DIR / 'embeddings_2024_500tok_contextual.npy'

print(f"[INFO] Input file: {INPUT_FILE}")
print(f"[INFO] Input exists: {INPUT_FILE.exists()}")
print(f"[INFO] Output directory: {OUTPUT_DIR}")

if INPUT_FILE.exists():
    file_size_mb = INPUT_FILE.stat().st_size / (1024*1024)
    print(f"[OK] Input file size: {file_size_mb:,.2f} MB")
else:
    print("[FAIL] Input file not found!")
    sys.exit(1)

# Install sentence-transformers if needed
try:
    from sentence_transformers import SentenceTransformer
    print("[OK] sentence-transformers already installed")
except ImportError:
    print("[INFO] Installing sentence-transformers...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers", "-q"])
    from sentence_transformers import SentenceTransformer
    print("[OK] sentence-transformers installed")

# Load Sentence Transformer Model
print(f"\n{'='*80}")
print(f"LOADING EMBEDDING MODEL")
print(f"{'='*80}\n")
print("[INFO] Loading sentence-transformers/all-MiniLM-L6-v2...")
print("[INFO] This will download ~80 MB on first run\n")

start_time = time.time()
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
load_time = time.time() - start_time

print(f"\n[OK] Model loaded in {load_time:.2f} seconds")
print(f"[INFO] Model details:")
print(f"  - Model name: all-MiniLM-L6-v2")
print(f"  - Embedding dimensions: {model.get_sentence_embedding_dimension()}")
print(f"  - Max sequence length: {model.max_seq_length} tokens")
print(f"  - Device: {model.device}")

# Load Processed Chunks
print(f"\n{'='*80}")
print(f"LOADING PROCESSED CHUNKS")
print(f"{'='*80}\n")
print(f"[INFO] Loading processed chunks from {INPUT_FILE.name}...")

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"[OK] Loaded {len(data):,} filings")

# Extract texts for embedding
embedding_texts = []
chunk_metadata = []

for filing in data:
    for chunk in filing['chunks']:
        # Use 'text_for_embedding' - the extended version with context!
        embedding_texts.append(chunk['text_for_embedding'])

        # Store metadata for later (ChromaDB step)
        chunk_metadata.append({
            'file_name': filing['file_name'],
            'company': chunk['metadata']['company'],
            'form_type': chunk['metadata']['form_type'],
            'filing_date': chunk['metadata']['filing_date'],
            'cik': chunk['metadata']['cik'],
            'chunk_id': chunk['chunk_id'],
            'chunk_index': chunk['metadata']['chunk_index'],
            'core_tokens': chunk['metadata']['core_tokens'],
            'extended_tokens': chunk['metadata']['extended_tokens']
        })

print(f"\n[OK] Extracted {len(embedding_texts):,} chunks for embedding")
print(f"[INFO] Using 'text_for_embedding' field (extended with approximately 700 tokens)")

# Preview first chunk
print(f"\n[Preview] First chunk text (first 400 chars):")
print(embedding_texts[0][:400])

# Generate Embeddings
print(f"\n{'='*80}")
print(f"EMBEDDING GENERATION")
print(f"{'='*80}")
print(f"\nStarting embedding generation...")
print(f"  Total chunks: {len(embedding_texts):,}")
print(f"  Batch size: 32")
print(f"  Device: {model.device}")
print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\nThis will take approximately 1-2 hours...\n")

start_time = time.time()

# Generate embeddings
embeddings = model.encode(
    embedding_texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True,  # Important for cosine similarity!
    device=None  # Auto-detect (use GPU if available)
)

embedding_time = time.time() - start_time

print(f"\n{'='*80}")
print(f"EMBEDDING GENERATION COMPLETE")
print(f"{'='*80}")
print(f"\nGeneration time: {embedding_time:.2f} seconds ({embedding_time/60:.2f} minutes)")
print(f"Speed: {len(embedding_texts) / embedding_time:.2f} chunks/second")
print(f"\nEmbeddings shape: {embeddings.shape}")
print(f"Expected: [{len(embedding_texts):,}, 384]")
print(f"\nEmbedding statistics:")
print(f"  Min value: {embeddings.min():.6f}")
print(f"  Max value: {embeddings.max():.6f}")
print(f"  Mean: {embeddings.mean():.6f}")
print(f"  Std: {embeddings.std():.6f}")

# Validate Embeddings
print(f"\n{'='*80}")
print(f"VALIDATION")
print(f"{'='*80}\n")
print(f"[INFO] Running validation checks...\n")

# Check 1: Correct shape
assert embeddings.shape == (len(embedding_texts), 384), "Incorrect embedding shape!"
print("[OK] Shape check passed")

# Check 2: No NaN or Inf values
assert not np.isnan(embeddings).any(), "NaN values found in embeddings!"
assert not np.isinf(embeddings).any(), "Inf values found in embeddings!"
print("[OK] No NaN/Inf values")

# Check 3: Embeddings are normalized (L2 norm ≈ 1)
norms = np.linalg.norm(embeddings, axis=1)
assert np.allclose(norms, 1.0, atol=1e-6), "Embeddings not properly normalized!"
print(f"[OK] Embeddings normalized (L2 norm = {norms.mean():.6f})")

# Check 4: Test similarity between similar chunks
similarity = np.dot(embeddings[0], embeddings[0])
print(f"[OK] Self-similarity check: {similarity:.6f} (should be ~1.0)")

similarity_adjacent = np.dot(embeddings[0], embeddings[1])
print(f"[INFO] Adjacent chunk similarity: {similarity_adjacent:.6f}")

print(f"\n[SUCCESS] All validation checks passed!")

# Save Embeddings
print(f"\n{'='*80}")
print(f"SAVING OUTPUTS")
print(f"{'='*80}\n")
print(f"[INFO] Saving embeddings to {OUTPUT_FILE}...")

np.save(OUTPUT_FILE, embeddings)

file_size_mb = OUTPUT_FILE.stat().st_size / (1024*1024)

print(f"[OK] Embeddings saved!")
print(f"  File: {OUTPUT_FILE.name}")
print(f"  Size: {file_size_mb:,.2f} MB")

# Save metadata
metadata_file = OUTPUT_DIR / 'chunk_metadata_2024.json'
with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(chunk_metadata, f, indent=2)

metadata_size_mb = metadata_file.stat().st_size / (1024*1024)
print(f"\n[OK] Metadata saved!")
print(f"  File: {metadata_file.name}")
print(f"  Size: {metadata_size_mb:,.2f} MB")

# Summary Statistics
print(f"\n{'='*80}")
print(f"EMBEDDING GENERATION SUMMARY")
print(f"{'='*80}")

print(f"\nModel:")
print(f"  Name: sentence-transformers/all-MiniLM-L6-v2")
print(f"  Dimensions: 384")
print(f"  Parameters: 22.7M")
print(f"  Device: {model.device}")

print(f"\nData:")
print(f"  Input file: {INPUT_FILE.name}")
print(f"  Total filings: {len(data):,}")
print(f"  Total chunks: {len(embedding_texts):,}")
print(f"  Avg chunks/filing: {len(embedding_texts) / len(data):.1f}")

print(f"\nPerformance:")
print(f"  Generation time: {embedding_time:.2f} seconds ({embedding_time/60:.2f} minutes)")
print(f"  Speed: {len(embedding_texts) / embedding_time:.2f} chunks/second")
print(f"  Speed: {len(embedding_texts) / embedding_time * 60:.0f} chunks/minute")

print(f"\nOutput:")
print(f"  Embeddings file: {OUTPUT_FILE.name}")
print(f"  Embeddings size: {file_size_mb:,.2f} MB")
print(f"  Embeddings shape: {embeddings.shape}")
print(f"  Metadata file: {metadata_file.name}")
print(f"  Metadata size: {metadata_size_mb:,.2f} MB")

print(f"\nStorage breakdown:")
print(f"  Per-chunk embedding: {384 * 4 / 1024:.2f} KB (384 dims × 4 bytes)")
print(f"  Total embeddings: {file_size_mb:,.2f} MB")

print(f"\nNext steps:")
print(f"  1. Option A: Simple RAG - Load into ChromaDB for basic retrieval testing")
print(f"  2. Option B: RAPTOR - Implement clustering (UMAP + GMM) and summarization")
print(f"  3. Run experimental comparison: Baseline vs Simple RAG vs RAPTOR RAG")
print(f"  4. Evaluate with RAGAS framework")

print(f"\nResearch citations:")
print(f"  - Sentence-BERT: https://arxiv.org/abs/1908.10084")
print(f"  - MTEB Benchmark: https://arxiv.org/abs/2210.07316")
print(f"  - RAPTOR Paper: https://arxiv.org/abs/2401.18059")
print(f"  - MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard")

print(f"\n{'='*80}")
print(f"ALL DONE!")
print(f"{'='*80}")
