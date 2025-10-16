"""
Execute 02_text_processing.ipynb cells
Process all 26,018 2024 SEC filings with contextual chunking
"""

import sys
from pathlib import Path
import re
import json
import zipfile
from collections import defaultdict
import time

# Add project root to path
project_root = Path.cwd().parent.parent
sys.path.insert(0, str(project_root))

# Data locations
DATA_ZIP = project_root / 'data' / 'external' / '10-X_C_2024.zip'
OUTPUT_DIR = project_root / 'notebooks' / 'prototyping' / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"[INFO] Data source: {DATA_ZIP}")
print(f"[INFO] Output directory: {OUTPUT_DIR}")
print(f"[INFO] Zip file exists: {DATA_ZIP.exists()}")

if DATA_ZIP.exists():
    zip_size_mb = DATA_ZIP.stat().st_size / (1024*1024)
    print(f"[OK] Zip file size: {zip_size_mb:.2f} MB")
else:
    print("[FAIL] Zip file not found!")
    sys.exit(1)

# Inspect 2024 Data Structure
print(f"\n{'='*80}")
print(f"INSPECTING ZIP CONTENTS")
print(f"{'='*80}\n")

with zipfile.ZipFile(DATA_ZIP, 'r') as z:
    file_list = z.namelist()

print(f"[OK] Total files in zip: {len(file_list):,}")
print(f"\n[INFO] First 10 files:")
for f in file_list[:10]:
    print(f"  {f}")

# Count by quarter
quarters = defaultdict(int)
for f in file_list:
    if 'QTR' in f:
        qtr = f.split('/')[1] if '/' in f else 'unknown'
        quarters[qtr] += 1

print(f"\n[INFO] Files by quarter:")
for qtr in sorted(quarters.keys()):
    print(f"  {qtr}: {quarters[qtr]:,} files")

# Filter to .txt files only
txt_files = [f for f in file_list if f.endswith('.txt')]
print(f"\n[OK] Text files to process: {len(txt_files):,}")

# Text Extraction Functions
def extract_sraf_metadata(content):
    """Extract metadata from SRAF header"""
    metadata = {}

    sec_header_match = re.search(r'<SEC-Header>(.*?)</SEC-Header>', content, re.DOTALL | re.IGNORECASE)
    if sec_header_match:
        sec_header = sec_header_match.group(1)

        field_mappings = {
            'COMPANY_NAME': [
                r'COMPANY CONFORMED NAME:\s*(.+?)(?:\n|$)',
                r'CONFORMED-NAME:\s*(.+?)(?:\n|$)',
                r'CONFORMED NAME:\s*(.+?)(?:\n|$)'
            ],
            'CIK': [
                r'CENTRAL INDEX KEY:\s*(.+?)(?:\n|$)',
                r'CIK:\s*(.+?)(?:\n|$)'
            ],
            'FORM_TYPE': [
                r'FORM TYPE:\s*(.+?)(?:\n|$)',
                r'FORM-TYPE:\s*(.+?)(?:\n|$)',
                r'CONFORMED SUBMISSION TYPE:\s*(.+?)(?:\n|$)'
            ],
            'FILING_DATE': [
                r'FILED AS OF DATE:\s*(.+?)(?:\n|$)',
                r'FILED-AS-OF-DATE:\s*(.+?)(?:\n|$)',
                r'DATE AS OF CHANGE:\s*(.+?)(?:\n|$)'
            ],
            'ACCESSION_NUMBER': [
                r'ACCESSION NUMBER:\s*(.+?)(?:\n|$)',
                r'ACCESSION-NUMBER:\s*(.+?)(?:\n|$)'
            ],
            'PERIOD_OF_REPORT': [
                r'CONFORMED PERIOD OF REPORT:\s*(.+?)(?:\n|$)',
                r'CONFORMED-PERIOD-OF-REPORT:\s*(.+?)(?:\n|$)'
            ]
        }

        for field, patterns in field_mappings.items():
            for pattern in patterns:
                match = re.search(pattern, sec_header, re.IGNORECASE)
                if match:
                    metadata[field] = match.group(1).strip()
                    break

    return metadata


def extract_clean_text(content):
    """Extract clean text content from SRAF-XML-wrapper"""
    text = re.sub(r'<Header>.*?</Header>', '', content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<SEC-Header>.*?</SEC-Header>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'<[^>]*xbrl[^>]*>.*?</[^>]*xbrl[^>]*>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

print(f"\n[OK] Text extraction functions loaded")

# Install tiktoken if needed
try:
    import tiktoken
    print("[OK] tiktoken already installed")
except ImportError:
    print("[INFO] Installing tiktoken...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tiktoken", "-q"])
    import tiktoken
    print("[OK] tiktoken installed")

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    """Count tokens in text using tiktoken"""
    return len(tokenizer.encode(text))


def contextual_chunk_filing(text, chunk_size=500, context_window=50):
    """Chunk text with contextual embeddings (Anthropic method)"""
    tokens = tokenizer.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))

        # Core chunk
        core_tokens = tokens[start:end]
        core_text = tokenizer.decode(core_tokens)

        # Extended chunk for embedding
        extended_start = max(0, start - context_window)
        extended_end = min(len(tokens), end + context_window)
        extended_tokens = tokens[extended_start:extended_end]
        extended_text = tokenizer.decode(extended_tokens)

        chunks.append({
            'core_text': core_text,
            'extended_text': extended_text,
            'core_start': start,
            'core_end': end,
            'core_tokens': len(core_tokens),
            'extended_tokens': len(extended_tokens)
        })

        start = end

    return chunks


def create_contextual_chunks(chunks, metadata):
    """Add document metadata headers to chunks"""
    contextual_chunks = []

    company = metadata.get('COMPANY_NAME', 'Unknown Company')
    form_type = metadata.get('FORM_TYPE', 'Unknown Form')
    filing_date = metadata.get('FILING_DATE', 'Unknown Date')
    cik = metadata.get('CIK', 'Unknown CIK')

    context_header = f"Document: {company} ({form_type}) filed {filing_date} [CIK: {cik}]\n\n"

    for i, chunk in enumerate(chunks):
        contextual_chunks.append({
            'chunk_id': i,
            'text': chunk['core_text'],
            'text_for_embedding': context_header + chunk['extended_text'],
            'metadata': {
                'company': company,
                'form_type': form_type,
                'filing_date': filing_date,
                'cik': cik,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'core_tokens': chunk['core_tokens'],
                'extended_tokens': chunk['extended_tokens']
            }
        })

    return contextual_chunks

print(f"[OK] Contextual chunking functions loaded")
print(f"[INFO] Core chunk size: 500 tokens")
print(f"[INFO] Context window: 50 tokens before + 50 tokens after = 100 total")

# Test on sample filing first
print(f"\n{'='*80}")
print(f"TESTING ON SAMPLE FILING")
print(f"{'='*80}\n")

with zipfile.ZipFile(DATA_ZIP, 'r') as z:
    sample_file = txt_files[0]
    print(f"[INFO] Testing with: {sample_file}")

    with z.open(sample_file) as f:
        raw_content = f.read().decode('utf-8', errors='ignore')

print(f"[OK] Loaded {len(raw_content):,} characters")

metadata = extract_sraf_metadata(raw_content)
clean_text = extract_clean_text(raw_content)

print(f"\n[OK] Extracted metadata:")
for key, value in metadata.items():
    print(f"  {key}: {value}")

print(f"\n[OK] Clean text length: {len(clean_text):,} characters")

token_count = count_tokens(clean_text)
raw_chunks = contextual_chunk_filing(clean_text, chunk_size=500, context_window=50)
contextual_chunks = create_contextual_chunks(raw_chunks, metadata)

print(f"\n[OK] Contextual chunking results:")
print(f"  Total tokens: {token_count:,}")
print(f"  Total chunks: {len(contextual_chunks)}")
print(f"  Avg core tokens/chunk: {sum(c['metadata']['core_tokens'] for c in contextual_chunks) / len(contextual_chunks):.0f}")
print(f"  Avg extended tokens/chunk: {sum(c['metadata']['extended_tokens'] for c in contextual_chunks) / len(contextual_chunks):.0f}")

print(f"\n[Preview] First chunk CORE text (what we store):")
print(contextual_chunks[0]['text'][:400])

print(f"\n[OK] Sample test successful!")

# Process all files
def process_filing_contextual(file_content, file_name, chunk_size=500, context_window=50):
    """Complete processing pipeline for a single filing"""
    metadata = extract_sraf_metadata(file_content)
    clean_text = extract_clean_text(file_content)
    raw_chunks = contextual_chunk_filing(clean_text, chunk_size, context_window)
    contextual_chunks = create_contextual_chunks(raw_chunks, metadata)

    return {
        'file_name': file_name,
        'metadata': metadata,
        'total_tokens': count_tokens(clean_text),
        'chunk_size': chunk_size,
        'context_window': context_window,
        'num_chunks': len(contextual_chunks),
        'chunks': contextual_chunks
    }

print(f"\n{'='*80}")
print(f"PROCESSING ALL 2024 FILINGS")
print(f"{'='*80}\n")
print(f"[INFO] Core chunk: 500 tokens")
print(f"[INFO] Context window: 50 tokens before + 50 after\n")

results = []
errors = []
start_time = time.time()

with zipfile.ZipFile(DATA_ZIP, 'r') as z:
    total_files = len(txt_files)
    print(f"[INFO] Total files to process: {total_files:,}\n")

    for i, file_path in enumerate(txt_files, 1):
        try:
            with z.open(file_path) as f:
                content = f.read().decode('utf-8', errors='ignore')

            result = process_filing_contextual(content, file_path, chunk_size=500, context_window=50)
            results.append(result)

            if i % 1000 == 0:
                elapsed = time.time() - start_time
                pct = (i / total_files) * 100
                rate = i / elapsed if elapsed > 0 else 0
                eta_seconds = (total_files - i) / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60
                print(f"[Progress] {i:,}/{total_files:,} ({pct:.1f}%) - {rate:.1f} files/sec - ETA: {eta_minutes:.1f} min")

        except Exception as e:
            errors.append({'file': file_path, 'error': str(e)})
            if len(errors) <= 10:
                print(f"[FAIL] {file_path}: {str(e)}")

processing_time = time.time() - start_time

print(f"\n{'='*80}")
print(f"PROCESSING COMPLETE")
print(f"{'='*80}")
print(f"Successfully processed: {len(results):,} filings")
print(f"Errors encountered: {len(errors)}")
print(f"Processing time: {processing_time:.1f} seconds ({processing_time/60:.1f} minutes)")
print(f"Rate: {len(results)/processing_time:.1f} files/second")

# Summary statistics
import numpy as np

total_chunks = sum(f['num_chunks'] for f in results)
total_tokens = sum(f['total_tokens'] for f in results)
avg_chunks = total_chunks / len(results) if results else 0
avg_tokens = total_tokens / len(results) if results else 0

total_core_tokens = sum(
    sum(c['metadata']['core_tokens'] for c in f['chunks'])
    for f in results
)
total_extended_tokens = sum(
    sum(c['metadata']['extended_tokens'] for c in f['chunks'])
    for f in results
)

chunks_per_filing = [f['num_chunks'] for f in results]
tokens_per_filing = [f['total_tokens'] for f in results]

print(f"\n{'='*80}")
print(f"SUMMARY STATISTICS")
print(f"{'='*80}")
print(f"\nDataset:")
print(f"  Total filings: {len(results):,}")
print(f"  Time period: 2024 (full year)")

print(f"\nChunking Configuration:")
print(f"  Core chunk size: 500 tokens")
print(f"  Context window: 100 tokens (50 before + 50 after)")
print(f"  Total chunks: {total_chunks:,}")
print(f"  Avg chunks/filing: {avg_chunks:.1f}")

print(f"\nToken Statistics:")
print(f"  Total document tokens: {total_tokens:,}")
print(f"  Total core tokens (stored): {total_core_tokens:,}")
print(f"  Total extended tokens (embedded): {total_extended_tokens:,}")
print(f"  Context overhead: {((total_extended_tokens / total_core_tokens) - 1) * 100:.1f}%")
print(f"  Avg tokens/filing: {avg_tokens:,.0f}")
print(f"  Min tokens/filing: {min(tokens_per_filing):,}")
print(f"  Max tokens/filing: {max(tokens_per_filing):,}")

# Export results
print(f"\n{'='*80}")
print(f"EXPORTING RESULTS")
print(f"{'='*80}\n")

output_file = OUTPUT_DIR / 'processed_2024_500tok_contextual.json'
print(f"[INFO] Saving to {output_file}...")

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

file_size_mb = output_file.stat().st_size / (1024*1024)

print(f"[OK] Saved: {output_file.name}")
print(f"[OK] File size: {file_size_mb:,.2f} MB")

if errors:
    error_file = OUTPUT_DIR / 'processing_errors_2024.json'
    with open(error_file, 'w', encoding='utf-8') as f:
        json.dump(errors, f, indent=2)
    print(f"[INFO] Error log saved: {error_file.name}")

print(f"\n{'='*80}")
print(f"ALL DONE!")
print(f"{'='*80}")
print(f"\nOutput files:")
print(f"  - {output_file.name} ({file_size_mb:,.2f} MB)")
if errors:
    print(f"  - processing_errors_2024.json ({len(errors)} errors)")

print(f"\nNext steps:")
print(f"1. Run 03_embedding_generation.ipynb to generate embeddings")
print(f"2. Use 'text_for_embedding' field for embedding generation")
print(f"3. Store only 'text' field (no storage overhead)")

print(f"\nResearch sources:")
print(f"  - Anthropic: https://www.anthropic.com/news/contextual-retrieval")
print(f"  - RAPTOR: https://arxiv.org/abs/2401.18059")
