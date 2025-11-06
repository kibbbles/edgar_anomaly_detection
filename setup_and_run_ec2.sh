#!/bin/bash
# Setup and Run Embedding Generation on EC2

echo "================================================================================"
echo "EC2 EMBEDDING SETUP - Preparing to generate 2.7M embeddings with GPU"
echo "================================================================================"

# Step 1: Create directory structure
echo ""
echo "[1/6] Creating directory structure..."
sudo mkdir -p /app/data/processed/2024_filings
sudo mkdir -p /app/data/embeddings/2024
sudo chown -R kabe:kabe /app/data

# Step 2: Move files into place
echo ""
echo "[2/6] Moving files into Docker-accessible locations..."
sudo cp ~/processed_2024_500tok_contextual.json /app/data/processed/2024_filings/
sudo cp ~/embed_all_2024_ec2.py /app/
sudo chown -R kabe:kabe /app

# Step 3: Check Docker container
echo ""
echo "[3/6] Checking Docker container status..."
docker ps | grep edgar-chunking

# Step 4: Install required Python packages in container
echo ""
echo "[4/6] Installing required packages in Docker container..."
docker exec edgar-chunking pip install sentence-transformers pandas pyarrow torch tqdm

# Step 5: Check for GPU
echo ""
echo "[5/6] Checking GPU availability..."
docker exec edgar-chunking nvidia-smi || echo "No GPU detected - will use CPU"

# Step 6: Run embedding generation
echo ""
echo "[6/6] Starting embedding generation..."
echo "This will take 30-60 minutes with GPU, or 2-3 hours with CPU"
echo ""
echo "Running in background with nohup..."
docker exec edgar-chunking nohup python /app/embed_all_2024_ec2.py > /app/embedding_log.txt 2>&1 &

echo ""
echo "================================================================================"
echo "SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "Embedding generation is now running in the background!"
echo ""
echo "To monitor progress:"
echo "  docker exec edgar-chunking tail -f /app/embedding_log.txt"
echo ""
echo "To check if it's still running:"
echo "  docker exec edgar-chunking ps aux | grep embed"
echo ""
echo "Output will be saved to:"
echo "  /app/data/embeddings/2024/embeddings.parquet"
echo "  /app/data/embeddings/2024/metadata.parquet"
echo "  /app/data/embeddings/2024/retrieval_texts.parquet"
echo ""
echo "================================================================================"
