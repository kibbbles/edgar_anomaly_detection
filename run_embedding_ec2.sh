#!/bin/bash
# Run Embedding Generation on EC2 - Using Existing Files
# This script uses the 26,000 individual JSON files already on EC2

echo "================================================================================"
echo "EC2 EMBEDDING GENERATION - 2024 SEC Filings (26,014 filings -> 2.7M chunks)"
echo "================================================================================"

# Step 1: Move script into /app
echo ""
echo "[1/5] Moving script to /app..."
sudo cp ~/embed_2024_from_ec2_files.py /app/
sudo chown kabe:kabe /app/embed_2024_from_ec2_files.py
echo "[OK] Script moved to /app/embed_2024_from_ec2_files.py"

# Step 2: Check Docker container status
echo ""
echo "[2/5] Checking Docker container..."
if docker ps | grep -q edgar-chunking; then
    echo "[OK] Container edgar-chunking is running"
else
    echo "[WARN] Container edgar-chunking not running. Starting it..."
    docker start edgar-chunking || echo "[ERROR] Failed to start container"
fi

# Step 3: Verify processed files exist
echo ""
echo "[3/5] Verifying processed files on EC2..."
if [ -d "/app/data/processed/2024/QTR1" ]; then
    QTR1_COUNT=$(find /app/data/processed/2024/QTR1 -name "*.json" | wc -l)
    echo "[OK] QTR1 found: $QTR1_COUNT files"
else
    echo "[ERROR] QTR1 directory not found!"
fi

# Step 4: Install required packages in Docker container
echo ""
echo "[4/5] Installing Python packages in Docker container..."
docker exec edgar-chunking pip install -q sentence-transformers pandas pyarrow torch tqdm
echo "[OK] Packages installed"

# Step 5: Check GPU availability
echo ""
echo "[5/5] Checking GPU availability..."
if docker exec edgar-chunking nvidia-smi > /dev/null 2>&1; then
    echo "[OK] GPU detected!"
    docker exec edgar-chunking nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "[WARN] No GPU detected - will use CPU (much slower)"
fi

# Run embedding generation
echo ""
echo "================================================================================"
echo "STARTING EMBEDDING GENERATION"
echo "================================================================================"
echo ""
echo "Source: /app/data/processed/2024/QTR*/*.json (26,000+ files)"
echo "Output: /app/data/embeddings/2024/*.parquet"
echo "Expected time: 30-60 minutes with GPU, 2-3 hours with CPU"
echo ""
echo "Running in background with nohup..."
docker exec edgar-chunking nohup python /app/embed_2024_from_ec2_files.py > /app/embedding_log.txt 2>&1 &

echo ""
echo "================================================================================"
echo "SETUP COMPLETE - Embedding generation is running in background"
echo "================================================================================"
echo ""
echo "To monitor progress:"
echo "  docker exec edgar-chunking tail -f /app/embedding_log.txt"
echo ""
echo "To check if still running:"
echo "  docker exec edgar-chunking ps aux | grep embed"
echo ""
echo "Expected output files:"
echo "  /app/data/embeddings/2024/embeddings.parquet (~150-200 MB)"
echo "  /app/data/embeddings/2024/metadata.parquet (~50-100 MB)"
echo "  /app/data/embeddings/2024/retrieval_texts.parquet (~500-800 MB)"
echo ""
echo "================================================================================"
