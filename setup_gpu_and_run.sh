#!/bin/bash
# Setup GPU support and run embedding generation
# Run on EC2 with: bash setup_gpu_and_run.sh

echo "================================================================================"
echo "EC2 GPU SETUP AND EMBEDDING GENERATION"
echo "================================================================================"

# Step 1: Install NVIDIA Container Toolkit
echo ""
echo "[1/6] Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Step 2: Configure Docker
echo ""
echo "[2/6] Configuring Docker for GPU..."
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Step 3: Test GPU access
echo ""
echo "[3/6] Testing GPU access in Docker..."
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Step 4: Remove old container and create new one with GPU
echo ""
echo "[4/6] Creating edgar-processing container with GPU support..."
docker rm -f edgar-processing 2>/dev/null || true
docker run -d --name edgar-processing --gpus all -v /app/data:/app/data edgar-chunking tail -f /dev/null

# Step 5: Copy script and run embedding
echo ""
echo "[5/6] Starting embedding generation..."
docker cp ~/embed_2024_from_ec2_files.py edgar-processing:/app/
docker exec edgar-processing nohup python /app/embed_2024_from_ec2_files.py > /app/embedding_log.txt 2>&1 &

# Step 6: Show initial output
echo ""
echo "[6/6] Showing initial output..."
sleep 3
docker exec edgar-processing cat /app/embedding_log.txt

echo ""
echo "================================================================================"
echo "SETUP COMPLETE - Embedding generation running on GPU"
echo "================================================================================"
echo ""
echo "Monitor progress:"
echo "  docker exec edgar-processing tail -f /app/embedding_log.txt"
echo ""
echo "Check GPU usage:"
echo "  nvidia-smi"
echo ""
echo "Expected completion: 30-60 minutes"
echo "Output location: /app/data/embeddings/2024/*.parquet"
echo ""
echo "================================================================================"
