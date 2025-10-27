"""
Simple RAG Query Script for SEC Filing Embeddings

Tests retrieval and LLM answer generation on embedded chunks.

Usage:
    python -m src.pipeline.rag_query \
        --embeddings /app/data/embeddings/test_q1 \
        --query "What was Tesla's revenue in fiscal year 2023?"
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import requests


class SimpleRAG:
    """Simple RAG system for SEC filings."""

    def __init__(
        self,
        embeddings_path: Path,
        embedding_model: str = "sentence-transformers/multi-qa-mpnet-base-dot-v1",
        ollama_host: str = "http://localhost:11434",
        ollama_model: str = "llama3"
    ):
        """
        Initialize RAG system.

        Args:
            embeddings_path: Path to embeddings directory (contains embeddings.parquet + metadata.parquet)
            embedding_model: Sentence transformer model name
            ollama_host: Ollama API endpoint
            ollama_model: Ollama model name
        """
        self.embeddings_path = Path(embeddings_path)
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model

        print(f"[INFO] Loading RAG system...")
        print(f"  Embeddings: {embeddings_path}")
        print(f"  Model: {embedding_model}")
        print(f"  LLM: {ollama_model} @ {ollama_host}")

        # Load embedding model
        print(f"\n[INFO] Loading embedding model...")
        self.encoder = SentenceTransformer(embedding_model)
        print(f"[OK] Model loaded (dims: {self.encoder.get_sentence_embedding_dimension()})")

        # Load embeddings and metadata
        print(f"\n[INFO] Loading embeddings and metadata...")
        self.embeddings = pd.read_parquet(self.embeddings_path / "embeddings.parquet").values
        self.metadata = pd.read_parquet(self.embeddings_path / "metadata.parquet")

        print(f"[OK] Loaded {len(self.embeddings)} chunks")
        print(f"  Shape: {self.embeddings.shape}")
        print(f"  Files: {self.metadata['file_name'].nunique()}")

        # Load original chunk texts from JSON files
        print(f"\n[INFO] Loading chunk texts from source JSON files...")
        self._load_chunk_texts()

    def _load_chunk_texts(self):
        """Load chunk texts from the original JSON files."""
        import json

        # Get unique files from metadata
        files = self.metadata['file_name'].unique()

        # Assume JSON files are in /app/data/processed/2024/QTR1/
        # Adjust path as needed
        processed_dir = Path("/app/data/processed/2024/QTR1")

        # Map (file_name, chunk_id) -> text
        self.chunk_texts = {}

        for file_name in files:
            json_path = processed_dir / file_name.replace('.txt', '.json')

            if not json_path.exists():
                print(f"[WARN] JSON file not found: {json_path}")
                continue

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for chunk in data.get('chunks', []):
                key = (file_name, chunk['chunk_id'])
                self.chunk_texts[key] = chunk['text']

        print(f"[OK] Loaded {len(self.chunk_texts)} chunk texts")

    def retrieve(self, query: str, top_k: int = 5):
        """
        Retrieve most similar chunks for a query.

        Args:
            query: User question
            top_k: Number of chunks to retrieve

        Returns:
            List of (chunk_text, similarity_score, metadata) tuples
        """
        print(f"\n[SEARCH] Query: {query}")
        print(f"[SEARCH] Retrieving top {top_k} chunks...")

        # Encode query
        query_embedding = self.encoder.encode([query], normalize_embeddings=True)[0]

        # Compute dot-product similarity (embeddings are already normalized)
        similarities = np.dot(self.embeddings, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Retrieve chunks
        results = []
        for idx in top_indices:
            file_name = self.metadata.iloc[idx]['file_name']
            chunk_id = self.metadata.iloc[idx]['chunk_id']
            similarity = similarities[idx]

            # Get chunk text
            key = (file_name, chunk_id)
            chunk_text = self.chunk_texts.get(key, "[Text not found]")

            results.append({
                'text': chunk_text,
                'similarity': float(similarity),
                'file_name': file_name,
                'chunk_id': chunk_id
            })

        print(f"[OK] Retrieved {len(results)} chunks")
        return results

    def generate_answer(self, query: str, retrieved_chunks: list):
        """
        Generate answer using LLM with retrieved context.

        Args:
            query: User question
            retrieved_chunks: List of retrieved chunk dicts

        Returns:
            LLM-generated answer
        """
        print(f"\n[LLM] Generating answer with {len(retrieved_chunks)} chunks...")

        # Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Chunk {i}] (from {chunk['file_name']}, similarity: {chunk['similarity']:.3f})\n"
                f"{chunk['text'][:500]}..."  # Truncate for display
            )

        context = "\n\n".join(context_parts)

        # Build prompt
        prompt = f"""You are a financial analyst assistant. Answer the user's question based ONLY on the provided context from SEC filings.

Context from SEC Filings:
{context}

Question: {query}

Answer (be specific and cite which filing you're referencing):"""

        # Call Ollama API
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for factual answers
                        "num_predict": 300,  # Max tokens
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                print(f"[OK] Answer generated")
                return answer
            else:
                return f"[ERROR] Ollama API error: {response.status_code}"

        except Exception as e:
            return f"[ERROR] Failed to generate answer: {e}"

    def query(self, question: str, top_k: int = 5):
        """
        Full RAG query: retrieve + generate.

        Args:
            question: User question
            top_k: Number of chunks to retrieve

        Returns:
            Answer string
        """
        # Retrieve
        chunks = self.retrieve(question, top_k=top_k)

        # Generate answer
        answer = self.generate_answer(question, chunks)

        return answer, chunks


def main():
    parser = argparse.ArgumentParser(description="Query SEC filings using RAG")
    parser.add_argument(
        '--embeddings',
        type=str,
        required=True,
        help='Path to embeddings directory (e.g., /app/data/embeddings/test_q1)'
    )
    parser.add_argument(
        '--query',
        type=str,
        required=True,
        help='Question to ask'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of chunks to retrieve (default: 5)'
    )
    parser.add_argument(
        '--ollama-host',
        type=str,
        default='http://localhost:11434',
        help='Ollama API endpoint'
    )
    parser.add_argument(
        '--ollama-model',
        type=str,
        default='llama3',
        help='Ollama model name'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("SEC FILING RAG QUERY SYSTEM")
    print("=" * 80)

    # Initialize RAG
    rag = SimpleRAG(
        embeddings_path=args.embeddings,
        ollama_host=args.ollama_host,
        ollama_model=args.ollama_model
    )

    # Run query
    answer, chunks = rag.query(args.query, top_k=args.top_k)

    # Display results
    print("\n" + "=" * 80)
    print("QUERY RESULTS")
    print("=" * 80)

    print(f"\n[QUESTION] {args.query}")

    print(f"\n[RETRIEVED CHUNKS] (top {args.top_k})")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n  {i}. {chunk['file_name']}")
        print(f"     Similarity: {chunk['similarity']:.4f}")
        print(f"     Preview: {chunk['text'][:150]}...")

    print(f"\n[ANSWER]")
    print(answer)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
