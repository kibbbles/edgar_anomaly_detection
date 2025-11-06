"""
title: Custom RAG pipeline with ChromaDB
author: onyxgs
date: 2025-10-29
version: 1.0
license: MIT
description: A pipeline for retrieving relevant information from a ChromaDB knowledge base using multi-qa-mpnet-base-dot-v1 embeddings.
requirements: ollama, chromadb, sentence_transformers, tiktoken
"""
from typing import List, Union, Generator, Iterator

import requests
import chromadb
from sentence_transformers import SentenceTransformer

class Pipeline:
    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "custom_edgar_pipeline"
        self.name = "Custom Edgar Pipeline"
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")
        
        OLLAMA_BASE_URL = "http://host.docker.internal:11434"
        MODEL = "qwen3:1.7b"
        
        if "user" in body:
            print("######################################")
            print(f'# Orig Body: {body}\n\n')
            print(f"# Orig Message: {user_message}")
            print("######################################")
        
        model = SentenceTransformer('sentence-transformers/multi-qa-mpnet-base-dot-v1')
        embed = model.encode(user_message)
        
        # chromadb
        client = chromadb.HttpClient(host="host.docker.internal", port=8000)
        # Create or get collection for your documents
        collection = client.get_or_create_collection(name="test")
        
        # search documents
        results = collection.query(
            query_embeddings=[embed],
            n_results=5,
            include=['documents', 'metadatas', 'distances']
        )
        
        context = "\n\n".join(results['documents'][0])
        
        prompt = f"""Based on the following context, answer the question accurately and concisely.

Context:
{context}

Question: {user_message}

Answer:"""

        body['messages'][0]['content'] = prompt
    
        try:
            r = requests.post(
                url=f"{OLLAMA_BASE_URL}/v1/chat/completions",
                json={**body, "model": MODEL},
                stream=True,
            )
    
            r.raise_for_status()
    
            if body["stream"]:
                return r.iter_lines()
            else:
                return r.json()
        except Exception as e:
            return f"Error: {e}"