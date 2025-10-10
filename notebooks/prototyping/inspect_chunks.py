"""
Quick script to inspect processed chunks
Usage: python inspect_chunks.py
"""

import json
from pathlib import Path

def inspect_chunk_size(chunk_size, filing_idx=0, chunk_idx=5):
    """
    Inspect a specific chunk from a specific filing

    Args:
        chunk_size: Token size (200, 300, 400, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000, 8000)
        filing_idx: Which filing to look at (0-1374)
        chunk_idx: Which chunk to look at within that filing
    """
    file_path = Path(f'output/processed_samples_{chunk_size}tok.json')

    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return

    print(f"[INFO] Loading {file_path.name}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"[OK] Loaded {len(data)} filings\n")

    # Get the filing
    if filing_idx >= len(data):
        print(f"[ERROR] Filing index {filing_idx} out of range (max: {len(data)-1})")
        return

    filing = data[filing_idx]

    # Print filing info
    print("="*80)
    print(f"FILING {filing_idx + 1} of {len(data)}")
    print("="*80)
    print(f"File name: {filing['file_name']}")
    print(f"Total tokens: {filing['total_tokens']:,}")
    print(f"Chunk size: {filing['chunk_size']} tokens")
    print(f"Overlap: {filing['overlap']} tokens")
    print(f"Number of chunks: {filing['num_chunks']}\n")

    # Get the chunk
    if chunk_idx >= len(filing['chunks']):
        print(f"[ERROR] Chunk index {chunk_idx} out of range (max: {len(filing['chunks'])-1})")
        chunk_idx = 0
        print(f"[INFO] Showing chunk 0 instead")

    chunk = filing['chunks'][chunk_idx]

    # Print chunk info
    print("="*80)
    print(f"CHUNK {chunk['chunk_id'] + 1} of {chunk['metadata']['total_chunks']}")
    print("="*80)
    print(f"Company: {chunk['metadata']['company']}")
    print(f"Form: {chunk['metadata']['form_type']}")
    print(f"Filing date: {chunk['metadata']['filing_date']}")
    print(f"CIK: {chunk['metadata']['cik']}\n")

    # Print chunk text
    print("CHUNK TEXT:")
    print("-"*80)
    print(chunk['text'])
    print("-"*80)

    # Show stats
    chunk_length = len(chunk['text'])
    print(f"\nChunk length: {chunk_length:,} characters")
    print(f"Approximate words: {len(chunk['text'].split())}")


def compare_chunk_sizes(filing_idx=0, chunk_idx=5):
    """Compare the same chunk across different chunk sizes"""

    sizes_to_compare = [200, 500, 1000, 2000]

    for size in sizes_to_compare:
        print("\n\n")
        print("#"*80)
        print(f"# CHUNK SIZE: {size} TOKENS")
        print("#"*80)
        inspect_chunk_size(size, filing_idx, chunk_idx)
        input("\n[Press Enter to continue to next size...]")


def show_overlap(chunk_size, filing_idx=0, chunk_idx=5):
    """Show overlap between two consecutive chunks"""

    file_path = Path(f'output/processed_samples_{chunk_size}tok.json')

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    filing = data[filing_idx]

    if chunk_idx + 1 >= len(filing['chunks']):
        print(f"[ERROR] Can't show overlap - chunk {chunk_idx} is the last chunk")
        return

    chunk1 = filing['chunks'][chunk_idx]
    chunk2 = filing['chunks'][chunk_idx + 1]

    print("="*80)
    print(f"OVERLAP BETWEEN CHUNKS {chunk_idx} and {chunk_idx + 1}")
    print("="*80)
    print(f"\nEND OF CHUNK {chunk_idx}:")
    print("-"*80)
    print(chunk1['text'][-400:])  # Last 400 chars

    print(f"\n\nSTART OF CHUNK {chunk_idx + 1}:")
    print("-"*80)
    print(chunk2['text'][:400])  # First 400 chars


if __name__ == '__main__':
    print("="*80)
    print("CHUNK INSPECTION TOOL")
    print("="*80)
    print("\nWhat would you like to do?")
    print("1. Inspect a specific chunk")
    print("2. Compare chunk sizes for same content")
    print("3. Check overlap between chunks")
    print("4. Quick demo (filing 0, chunk 5, size 500)")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == '1':
        chunk_size = int(input("Chunk size (200, 500, 1000, 2000, etc.): "))
        filing_idx = int(input("Filing index (0-1374): "))
        chunk_idx = int(input("Chunk index (0-N): "))
        inspect_chunk_size(chunk_size, filing_idx, chunk_idx)

    elif choice == '2':
        filing_idx = int(input("Filing index (0-1374): "))
        chunk_idx = int(input("Chunk index (0-N): "))
        compare_chunk_sizes(filing_idx, chunk_idx)

    elif choice == '3':
        chunk_size = int(input("Chunk size (200, 500, 1000, 2000, etc.): "))
        filing_idx = int(input("Filing index (0-1374): "))
        chunk_idx = int(input("First chunk index (0-N): "))
        show_overlap(chunk_size, filing_idx, chunk_idx)

    elif choice == '4':
        print("\n[INFO] Running quick demo: filing 0, chunk 5, 500 tokens")
        inspect_chunk_size(500, 0, 5)

    else:
        print("[ERROR] Invalid choice")
