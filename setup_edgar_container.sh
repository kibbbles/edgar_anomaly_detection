#!/bin/bash
# Setup Edgar Processing Container and Run Embeddings

echo "================================================================================"
echo "EDGAR PROCESSING CONTAINER SETUP"
echo "================================================================================"

cd /app/home/kabe

# Step 1: Build the Docker image
echo ""
echo "[1/4] Building edgar-processing Docker image..."
docker build -f Dockerfile.edgar -t edgar-processing .
echo "[OK] Image built"

# Step 2: Create and start the container with GPU support
echo ""
echo "[2/4] Creating edgar-processing container..."
docker run -d \
  --name edgar-processing \
  --gpus all \
  -v /app/data:/app/data \
  edgar-processing \
  tail -f /dev/null

echo "[OK] Container created and running"

# Step 3: Verify GPU in container
echo ""
echo "[3/4] Checking GPU availability in container..."
docker exec edgar-processing nvidia-smi || echo "[WARN] No GPU detected - will use CPU"

# Step 4: Verify processed files
echo ""
echo "[4/4] Verifying data access..."
docker exec edgar-processing ls -l /app/data/processed/2024/ | head -n 5
echo ""
docker exec edgar-processing sh -c "find /app/data/processed/2024/QTR1 -name '*.json' | wc -l"

echo ""
echo "================================================================================"
echo "CONTAINER READY - Now running embedding generation"
echo "================================================================================"
echo ""

# Run the embedding script
echo "Starting embedding generation in background..."
docker exec edgar-processing nohup python /app/embed_2024_from_ec2_files.py > /app/embedding_log.txt 2>&1 &

echo ""
echo "================================================================================"
echo "SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "Monitor progress:"
echo "  docker exec edgar-processing tail -f /app/embedding_log.txt"
echo ""
echo "Check status:"
echo "  docker exec edgar-processing ps aux | grep python"
echo ""
echo "Output location:"
echo "  /app/data/embeddings/2024/*.parquet"
echo ""
echo "================================================================================"
