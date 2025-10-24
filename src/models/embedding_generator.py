"""
Embedding Generator for SEC Filing Chunks

Generates high-dimensional embeddings (768-dim) for chunked SEC filings using
sentence-transformers/multi-qa-mpnet-base-dot-v1.

Features:
- 768-dimensional embeddings for precise retrieval
- Trained for Q&A tasks (perfect for "find X in filings" queries)
- Preserves financial/legal terminology distinctions
- Batch processing for efficiency
- Progress tracking with tqdm

Usage:
    python -m src.models.embedding_generator \
        --input /app/data/processed/2024/QTR4 \
        --output /app/data/embeddings/test \
        --files 20241024_10-Q_edgar_data_1318605_0001628280-24-043486.json \
                20241030_10-Q_edgar_data_789019_0000950170-24-118967.json \
                20241101_10-K_edgar_data_320193_0000320193-24-000123.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def load_chunks_from_files(input_dir: Path, filenames: List[str]) -> tuple[List[str], List[Dict[str, Any]]]:
    """
    Load chunks and metadata from specified JSON files.

    Args:
        input_dir: Directory containing chunked JSON files
        filenames: List of JSON filenames to process

    Returns:
        tuple: (texts, metadata_list)
            - texts: List of chunk texts for embedding
            - metadata_list: List of metadata dicts for each chunk
    """
    texts = []
    metadata_list = []

    print(f"\n[INFO] Loading chunks from {len(filenames)} files...")

    for filename in filenames:
        file_path = input_dir / filename

        if not file_path.exists():
            print(f"[WARN] File not found: {file_path}")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                filing_data = json.load(f)

            file_name = filing_data.get('file_name', filename)
            chunks = filing_data.get('chunks', [])

            for chunk in chunks:
                # Extract text for embedding
                text = chunk.get('text', '')

                # Extract metadata
                metadata = chunk.get('metadata', {})
                metadata['file_name'] = file_name
                metadata['chunk_id'] = chunk.get('chunk_id', '')

                texts.append(text)
                metadata_list.append(metadata)

            print(f"[OK] {filename}: {len(chunks)} chunks")

        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")

    print(f"\n[OK] Total chunks loaded: {len(texts):,}")
    return texts, metadata_list


def generate_embeddings(
    texts: List[str],
    model_name: str = 'sentence-transformers/multi-qa-mpnet-base-dot-v1',
    batch_size: int = 32
) -> np.ndarray:
    """
    Generate embeddings for text chunks.

    Args:
        texts: List of text chunks
        model_name: Sentence-transformers model name
        batch_size: Batch size for encoding

    Returns:
        np.ndarray: Embeddings matrix (n_chunks, 768)
    """
    print(f"\n[INFO] Loading embedding model: {model_name}...")
    print(f"[INFO] This will download ~420MB on first run\n")

    model = SentenceTransformer(model_name)

    print(f"[OK] Model loaded")
    print(f"  - Model: {model_name}")
    print(f"  - Dimensions: {model.get_sentence_embedding_dimension()}")
    print(f"  - Max sequence length: {model.max_seq_length} tokens")
    print(f"  - Device: {model.device}")

    print(f"\n[INFO] Generating embeddings for {len(texts):,} chunks...")
    print(f"[INFO] Batch size: {batch_size}")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # Normalize for dot-product similarity
        device=None  # Auto-detect (use GPU if available)
    )

    print(f"\n[OK] Embeddings generated")
    print(f"  - Shape: {embeddings.shape}")
    print(f"  - Expected: [{len(texts):,}, 768]")
    print(f"  - Normalized: Yes (L2 norm = 1.0)")

    return embeddings


def save_embeddings(
    embeddings: np.ndarray,
    metadata_list: List[Dict[str, Any]],
    output_dir: Path
):
    """
    Save embeddings and metadata to parquet files.

    Args:
        embeddings: Embeddings matrix
        metadata_list: List of metadata dicts
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save embeddings as parquet
    embeddings_file = output_dir / 'embeddings.parquet'
    embeddings_df = pd.DataFrame(embeddings)
    embeddings_df.to_parquet(embeddings_file, compression='snappy')

    embeddings_size_mb = embeddings_file.stat().st_size / (1024**2)
    print(f"\n[OK] Embeddings saved:")
    print(f"  - File: {embeddings_file}")
    print(f"  - Size: {embeddings_size_mb:.2f} MB")
    print(f"  - Format: Parquet (snappy compression)")

    # Save metadata as parquet
    metadata_file = output_dir / 'metadata.parquet'
    metadata_df = pd.DataFrame(metadata_list)
    metadata_df.to_parquet(metadata_file, compression='snappy')

    metadata_size_mb = metadata_file.stat().st_size / (1024**2)
    print(f"\n[OK] Metadata saved:")
    print(f"  - File: {metadata_file}")
    print(f"  - Size: {metadata_size_mb:.2f} MB")
    print(f"  - Rows: {len(metadata_df):,}")
    print(f"  - Columns: {list(metadata_df.columns)}")


def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for SEC filing chunks')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory containing chunked JSON files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for embeddings')
    parser.add_argument('--files', nargs='+', required=True,
                       help='List of JSON filenames to process')
    parser.add_argument('--model', type=str,
                       default='sentence-transformers/multi-qa-mpnet-base-dot-v1',
                       help='Sentence-transformers model name')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size for embedding generation')

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    print("=" * 80)
    print("SEC FILING EMBEDDING GENERATOR")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Input directory: {input_dir}")
    print(f"  Output directory: {output_dir}")
    print(f"  Files to process: {len(args.files)}")
    print(f"  Embedding model: {args.model}")
    print(f"  Batch size: {args.batch_size}")

    # Validate input directory
    if not input_dir.exists():
        print(f"\n[ERROR] Input directory does not exist: {input_dir}")
        sys.exit(1)

    # Load chunks
    texts, metadata_list = load_chunks_from_files(input_dir, args.files)

    if len(texts) == 0:
        print(f"\n[ERROR] No chunks loaded. Exiting.")
        sys.exit(1)

    # Generate embeddings
    embeddings = generate_embeddings(texts, model_name=args.model, batch_size=args.batch_size)

    # Validate embeddings
    print(f"\n[INFO] Validating embeddings...")
    assert embeddings.shape == (len(texts), 768), "Incorrect embedding shape"
    assert not np.isnan(embeddings).any(), "NaN values found"
    assert not np.isinf(embeddings).any(), "Inf values found"

    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-6), "Embeddings not normalized"
    print(f"[OK] All validation checks passed")

    # Save embeddings and metadata
    save_embeddings(embeddings, metadata_list, output_dir)

    print("\n" + "=" * 80)
    print("EMBEDDING GENERATION COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  Files processed: {len(args.files)}")
    print(f"  Total chunks: {len(texts):,}")
    print(f"  Embedding dimensions: 768")
    print(f"  Output location: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. Load embeddings: pd.read_parquet('{output_dir}/embeddings.parquet')")
    print(f"  2. Load metadata: pd.read_parquet('{output_dir}/metadata.parquet')")
    print(f"  3. Test similarity search with sample queries")
    print(f"  4. If quality is good, scale to full 2024 dataset")
    print("=" * 80)


if __name__ == '__main__':
    main()
