"""
Text processing and chunking for SEC filings.

This module handles:
1. Parsing cleaned SEC filing text files
2. Extracting metadata from file headers
3. Chunking text into 500-token segments
4. Generating 100-token contextual summaries for each chunk (using LLM)
5. Saving chunked data to JSON

Input: /app/data/edgar/extracted/{year}/QTR{n}/*.txt
Output: /app/data/processed/{year}/QTR{n}/*.json
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import tiktoken
from tqdm import tqdm
import requests


@dataclass
class FilingMetadata:
    """Metadata extracted from SEC filing header."""
    filename: str
    cik: str
    company_name: str
    form_type: str
    filing_date: str
    accession_number: str
    fiscal_year: Optional[str] = None
    gross_file_size: Optional[int] = None
    net_file_size: Optional[int] = None


@dataclass
class TextChunk:
    """A single text chunk with metadata."""
    chunk_id: int
    text: str
    token_count: int
    char_start: int
    char_end: int
    context_summary: Optional[str] = None  # LLM-generated context (100 tokens)


class TextProcessor:
    """Process SEC filing text files into chunked JSON."""

    def __init__(
        self,
        chunk_size: int = 500,
        context_size: int = 100,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize text processor.

        Args:
            chunk_size: Target tokens per chunk (default: 500)
            context_size: Tokens for contextual summary (default: 100)
            encoding_name: Tiktoken encoding to use
        """
        self.chunk_size = chunk_size
        self.context_size = context_size
        self.encoding = tiktoken.get_encoding(encoding_name)

    def extract_metadata(self, file_path: Path) -> FilingMetadata:
        """
        Extract metadata from SEC filing header.

        Args:
            file_path: Path to SEC filing .txt file

        Returns:
            FilingMetadata object
        """
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(10000)  # Read first 10KB for header

        # Extract from filename: YYYYMMDD_FORM-TYPE_edgar_data_CIK_ACCESSION.txt
        filename = file_path.name
        parts = filename.replace('.txt', '').split('_')

        filing_date = parts[0] if len(parts) > 0 else ''
        form_type = parts[1] if len(parts) > 1 else ''
        cik = parts[4] if len(parts) > 4 else ''
        accession = parts[5] if len(parts) > 5 else ''

        # Extract from <FileStats> header if present
        company_name = ''
        gross_size = None
        net_size = None

        # Extract company name from SEC-Header section
        company_match = re.search(r'COMPANY CONFORMED NAME:\s+(.+)', content)
        if company_match:
            company_name = company_match.group(1).strip()

        # Extract file sizes
        gross_match = re.search(r'<GrossFileSize>(\d+)</GrossFileSize>', content)
        if gross_match:
            gross_size = int(gross_match.group(1))

        net_match = re.search(r'<NetFileSize>(\d+)</NetFileSize>', content)
        if net_match:
            net_size = int(net_match.group(1))

        # Determine fiscal year from filing date (YYYYMMDD)
        fiscal_year = filing_date[:4] if filing_date else None

        return FilingMetadata(
            filename=filename,
            cik=cik,
            company_name=company_name,
            form_type=form_type,
            filing_date=filing_date,
            accession_number=accession,
            fiscal_year=fiscal_year,
            gross_file_size=gross_size,
            net_file_size=net_size
        )

    def extract_filing_text(self, file_path: Path) -> str:
        """
        Extract main filing text, removing header sections.

        Args:
            file_path: Path to SEC filing .txt file

        Returns:
            Cleaned filing text (after </Header>)
        """
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Remove everything before </Header> tag
        header_end = content.find('</Header>')
        if header_end != -1:
            content = content[header_end + len('</Header>'):]

        # Clean up extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 consecutive newlines
        content = re.sub(r' +', ' ', content)  # Collapse multiple spaces
        content = content.strip()

        return content

    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Chunk text into ~500 token segments.

        Args:
            text: Full filing text

        Returns:
            List of TextChunk objects
        """
        # Encode entire text to tokens
        tokens = self.encoding.encode(text)
        chunks = []

        chunk_id = 0
        current_pos = 0

        while current_pos < len(tokens):
            # Extract chunk tokens
            chunk_tokens = tokens[current_pos:current_pos + self.chunk_size]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            # Calculate character positions (approximate)
            char_start = len(self.encoding.decode(tokens[:current_pos]))
            char_end = char_start + len(chunk_text)

            chunks.append(TextChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                token_count=len(chunk_tokens),
                char_start=char_start,
                char_end=char_end,
                context_summary=None  # Generated later by LLM
            ))

            chunk_id += 1
            current_pos += self.chunk_size

        return chunks

    def generate_context_summary(
        self,
        chunk: TextChunk,
        metadata: FilingMetadata,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3",
        max_retries: int = 3
    ) -> str:
        """
        Generate 50-100 token contextual summary for a chunk using LLM.

        This implements Anthropic's contextual retrieval method: generate a brief
        summary explaining what the chunk discusses in relation to the whole document.

        Args:
            chunk: TextChunk to summarize
            metadata: Filing metadata for context
            ollama_host: Ollama API endpoint
            model: Ollama model name (qwen2.5:1.5b or llama3)
            max_retries: Maximum retry attempts on failure

        Returns:
            50-100 token context summary

        Example:
            Input chunk: "The company's revenue grew by 3% over the previous quarter"
            Output context: "This chunk is from ACME Corp's Q2 2023 10-Q filing discussing
                           quarterly revenue performance. Previous quarter revenue was $314M."
        """
        # Construct prompt following Anthropic's method
        prompt = f"""<document>
Company: {metadata.company_name}
Filing Type: {metadata.form_type}
Filing Date: {metadata.filing_date}
CIK: {metadata.cik}
</document>

Provide a brief, factual summary (50-100 tokens) explaining what this chunk discusses in relation to the full {metadata.form_type} filing. Focus on the specific topic, metrics, or section covered.

<chunk>
{chunk.text[:1000]}
</chunk>"""

        # Call Ollama API with retries
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Lower temperature for factual summaries
                            "num_predict": 100,  # Limit output to ~100 tokens
                        }
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    context = result.get('response', '').strip()

                    # Fallback if LLM returns empty
                    if not context:
                        return self._fallback_context(chunk, metadata)

                    return context

                else:
                    print(f"[WARN] Ollama API error (attempt {attempt + 1}/{max_retries}): {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"[WARN] Ollama request failed (attempt {attempt + 1}/{max_retries}): {e}")

            except Exception as e:
                print(f"[ERROR] Unexpected error generating context: {e}")

        # All retries failed - use fallback
        print(f"[WARN] All LLM retries failed for chunk {chunk.chunk_id}, using fallback context")
        return self._fallback_context(chunk, metadata)

    def _fallback_context(self, chunk: TextChunk, metadata: FilingMetadata) -> str:
        """
        Generate fallback context when LLM is unavailable.

        Args:
            chunk: TextChunk
            metadata: Filing metadata

        Returns:
            Template-based context string
        """
        return (
            f"This is chunk {chunk.chunk_id} from {metadata.company_name}'s "
            f"{metadata.form_type} filing dated {metadata.filing_date}. "
            f"Contains {chunk.token_count} tokens of filing content."
        )

    def process_file(
        self,
        input_path: Path,
        output_path: Path,
        generate_context: bool = False
    ) -> Dict:
        """
        Process a single SEC filing file.

        Args:
            input_path: Path to input .txt file
            output_path: Path to output .json file
            generate_context: Whether to generate LLM context summaries

        Returns:
            Processing statistics
        """
        # Extract metadata
        metadata = self.extract_metadata(input_path)

        # Extract filing text
        filing_text = self.extract_filing_text(input_path)

        # Chunk text
        chunks = self.chunk_text(filing_text)

        # Optionally generate context summaries
        if generate_context:
            for chunk in chunks:
                chunk.context_summary = self.generate_context_summary(chunk, metadata)

        # Prepare output data
        output_data = {
            "metadata": asdict(metadata),
            "num_chunks": len(chunks),
            "total_tokens": sum(c.token_count for c in chunks),
            "chunks": [asdict(c) for c in chunks]
        }

        # Write to JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return {
            "filename": metadata.filename,
            "num_chunks": len(chunks),
            "total_tokens": sum(c.token_count for c in chunks)
        }

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        generate_context: bool = False,
        file_limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Process all .txt files in a directory.

        Args:
            input_dir: Input directory (e.g., /app/data/edgar/extracted/2024/QTR1/)
            output_dir: Output directory (e.g., /app/data/processed/2024/QTR1/)
            generate_context: Whether to generate LLM context summaries
            file_limit: Optional limit on number of files to process (for testing)

        Returns:
            List of processing statistics
        """
        # Find all .txt files
        txt_files = sorted(input_dir.glob('*.txt'))

        if file_limit:
            txt_files = txt_files[:file_limit]

        results = []

        for txt_file in tqdm(txt_files, desc=f"Processing {input_dir.name}"):
            # Create corresponding output path
            output_file = output_dir / txt_file.name.replace('.txt', '.json')

            try:
                stats = self.process_file(txt_file, output_file, generate_context)
                results.append(stats)
            except Exception as e:
                print(f"[ERROR] Failed to process {txt_file.name}: {e}")
                results.append({
                    "filename": txt_file.name,
                    "error": str(e)
                })

        return results


def main():
    """Example usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Process SEC filing text files into chunks")
    parser.add_argument("--input", required=True, help="Input directory path")
    parser.add_argument("--output", required=True, help="Output directory path")
    parser.add_argument("--chunk-size", type=int, default=500, help="Tokens per chunk")
    parser.add_argument("--context-size", type=int, default=100, help="Tokens for context summary")
    parser.add_argument("--generate-context", action="store_true", help="Generate LLM context summaries")
    parser.add_argument("--limit", type=int, help="Limit number of files to process (for testing)")

    args = parser.parse_args()

    processor = TextProcessor(
        chunk_size=args.chunk_size,
        context_size=args.context_size
    )

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    print(f"Processing files from: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Chunk size: {args.chunk_size} tokens")
    print(f"Context size: {args.context_size} tokens")
    print(f"Generate context: {args.generate_context}")

    results = processor.process_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        generate_context=args.generate_context,
        file_limit=args.limit
    )

    # Print summary
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]

    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total files: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        total_chunks = sum(r['num_chunks'] for r in successful)
        total_tokens = sum(r['total_tokens'] for r in successful)
        print(f"Total chunks: {total_chunks:,}")
        print(f"Total tokens: {total_tokens:,}")

    if failed:
        print("\nFailed files:")
        for r in failed[:10]:  # Show first 10 failures
            print(f"  - {r['filename']}: {r['error']}")


if __name__ == "__main__":
    main()
