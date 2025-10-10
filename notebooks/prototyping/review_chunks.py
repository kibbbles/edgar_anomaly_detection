"""
Chunk Review Tool with Text Wrapping
Makes it easier to manually review chunk quality
"""

import json
import textwrap
from pathlib import Path


def wrap_text(text, width=80):
    """Wrap text to specified width while preserving intentional line breaks"""
    # Split by double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = []

    for para in paragraphs:
        # Remove single newlines within paragraph
        para = para.replace('\n', ' ')
        # Wrap paragraph
        wrapped = textwrap.fill(para, width=width)
        wrapped_paragraphs.append(wrapped)

    return '\n\n'.join(wrapped_paragraphs)


def review_chunk(chunk_size, filing_idx=0, chunk_idx=5):
    """
    Review a specific chunk with nice formatting

    Args:
        chunk_size: 200, 300, 400, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000, 8000
        filing_idx: Which filing (0-1374)
        chunk_idx: Which chunk within filing
    """
    file_path = Path(f'output/processed_samples_{chunk_size}tok.json')

    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    filing = data[filing_idx]

    if chunk_idx >= len(filing['chunks']):
        chunk_idx = 0
        print(f"[INFO] Chunk index out of range, showing chunk 0")

    chunk = filing['chunks'][chunk_idx]

    # Print header
    print("\n" + "="*80)
    print(f"CHUNK SIZE: {chunk_size} tokens | Filing {filing_idx + 1}/{len(data)} | Chunk {chunk_idx + 1}/{filing['num_chunks']}")
    print("="*80)
    print(f"File: {filing['file_name']}")
    print(f"Total tokens: {filing['total_tokens']:,} | Chunks: {filing['num_chunks']}")
    print("="*80)

    # Extract just the content (skip the "Document: Unknown..." header if present)
    text = chunk['text']
    if text.startswith('Document: Unknown Company'):
        # Skip to after the header
        lines = text.split('\n')
        if len(lines) > 2:
            text = '\n'.join(lines[2:])  # Skip first 2 lines (header + blank)

    # Wrap text for readability
    wrapped_text = wrap_text(text, width=80)

    # Print chunk content
    print("\nCHUNK CONTENT:")
    print("-"*80)
    print(wrapped_text)
    print("-"*80)

    # Stats
    word_count = len(text.split())
    print(f"\nStats: {len(text):,} characters | ~{word_count} words")
    print("\n")


def compare_sizes(filing_idx=0, chunk_idx=5):
    """Compare same chunk across 4 different sizes"""

    sizes = [200, 500, 1000, 2000]

    print("\n" + "#"*80)
    print(f"# COMPARING CHUNK SIZES: Filing {filing_idx}, Chunk {chunk_idx}")
    print("#"*80)

    for size in sizes:
        review_chunk(size, filing_idx, chunk_idx)

        if size != sizes[-1]:
            input("\n[Press Enter for next size...]")


def quick_scan(chunk_size, num_samples=5):
    """Quickly scan multiple chunks from one chunk size"""

    file_path = Path(f'output/processed_samples_{chunk_size}tok.json')

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("\n" + "="*80)
    print(f"QUICK SCAN: {chunk_size} tokens - Showing {num_samples} random chunks")
    print("="*80)

    import random
    random.seed(42)

    # Pick random filings
    sample_filings = random.sample(range(len(data)), min(num_samples, len(data)))

    for i, filing_idx in enumerate(sample_filings):
        filing = data[filing_idx]

        # Pick middle chunk
        chunk_idx = filing['num_chunks'] // 2

        print(f"\n{'='*80}")
        print(f"SAMPLE {i+1}/{num_samples}: Filing {filing_idx}, Middle chunk")
        print(f"{'='*80}")

        chunk = filing['chunks'][chunk_idx]
        text = chunk['text']

        # Skip header
        if text.startswith('Document: Unknown Company'):
            lines = text.split('\n')
            if len(lines) > 2:
                text = '\n'.join(lines[2:])

        # Show first 500 chars wrapped
        preview = text[:500] + "..." if len(text) > 500 else text
        wrapped = wrap_text(preview, width=80)

        print(wrapped)
        print()

        # Ask for evaluation
        print("Does this chunk feel:")
        print("  [C] Complete and coherent")
        print("  [F] Too fragmented/incomplete")
        print("  [L] Too long/mixing topics")
        print("  [S] Skip to next")

        response = input("\nYour evaluation (C/F/L/S): ").strip().upper()

        if response == 'S':
            continue


def evaluation_guide():
    """Print evaluation criteria"""

    print("\n" + "="*80)
    print("CHUNK EVALUATION GUIDE")
    print("="*80)

    print("""
What to look for when reviewing chunks:

✅ GOOD CHUNK (Complete & Coherent):
   - Contains a complete thought or idea
   - Has enough context to understand standalone
   - Covers one topic or closely related topics
   - Sentences are complete (not cut off)
   - Example: Full risk factor, complete financial table, entire section

❌ TOO FRAGMENTED (Too Small):
   - Sentences cut off mid-thought
   - Missing crucial context
   - Hard to understand what it's about
   - Feels incomplete
   - Example: Partial table row, sentence fragment

❌ TOO BROAD (Too Large):
   - Mixes unrelated topics
   - Includes lots of irrelevant information
   - Would retrieve noise when searching
   - Covers multiple distinct sections
   - Example: Revenue discussion + legal proceedings + risk factors all in one

IGNORE the "Unknown Company" headers - that's a metadata extraction bug for old
filings (1993-1995). Focus on the CONTENT QUALITY.

OPTIMAL SIZE (based on FinGPT research):
   - 500-1000 tokens for financial filings
   - Good balance of precision and context
   - Complete enough to understand, specific enough to retrieve precisely
""")

    print("="*80 + "\n")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("CHUNK REVIEW TOOL")
    print("="*80)

    print("\nOptions:")
    print("1. Review specific chunk")
    print("2. Compare chunk sizes (200 vs 500 vs 1000 vs 2000)")
    print("3. Quick scan (review 5 random chunks from one size)")
    print("4. Show evaluation guide")
    print("5. Quick demo (filing 10, chunk 5, size 500)")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == '1':
        chunk_size = int(input("Chunk size (200/300/400/500/750/1000/1500/2000/3000/4000/5000/8000): "))
        filing_idx = int(input("Filing index (0-1374, try 10-100 for newer filings): "))
        chunk_idx = int(input("Chunk index (0-N, try 5 for middle): "))
        review_chunk(chunk_size, filing_idx, chunk_idx)

    elif choice == '2':
        filing_idx = int(input("Filing index (0-1374, try 50 for a 90s filing): "))
        chunk_idx = int(input("Chunk index (try 5): "))
        compare_sizes(filing_idx, chunk_idx)

    elif choice == '3':
        chunk_size = int(input("Chunk size to scan (200/500/1000/2000): "))
        quick_scan(chunk_size)

    elif choice == '4':
        evaluation_guide()

    elif choice == '5':
        print("\n[Running demo: filing 10, chunk 5, 500 tokens]")
        review_chunk(500, 10, 5)
        print("\n[TIP: Try option 2 to compare sizes, or option 3 to scan multiple chunks]")

    else:
        print("[ERROR] Invalid choice")
