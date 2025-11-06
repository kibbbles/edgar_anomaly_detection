#!/bin/bash
# Run embedding generation directly on EC2 host (no Docker, no sudo needed)
# This will use the GPU directly without needing NVIDIA Container Toolkit

echo "================================================================================"
echo "EMBEDDING GENERATION ON EC2 HOST - Using GPU"
echo "================================================================================"

# Step 1: Install Python packages (user-level, no sudo needed)
echo ""
echo "[1/3] Installing Python packages..."
pip3 install --user sentence-transformers==2.2.2 torch pandas pyarrow tqdm numpy

# Step 2: Verify GPU access
echo ""
echo "[2/3] Checking GPU availability..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Step 3: Run embedding generation
echo ""
echo "[3/3] Starting embedding generation..."
echo "This will take 30-60 minutes with GPU"
echo "Output will be saved to: /app/data/embeddings/2024/"
echo ""

nohup python3 ~/embed_2024_from_ec2_files.py > ~/embedding_log.txt 2>&1 &
PYTHON_PID=$!

echo "Process started with PID: $PYTHON_PID"
echo ""
echo "================================================================================"
echo "EMBEDDING GENERATION RUNNING"
echo "================================================================================"
echo ""
echo "Monitor progress:"
echo "  tail -f ~/embedding_log.txt"
echo ""
echo "Check if still running:"
echo "  ps aux | grep embed"
echo ""
echo "Check GPU usage:"
echo "  nvidia-smi"
echo ""
echo "================================================================================"

# Show initial output
sleep 3
echo ""
echo "Initial output:"
head -n 20 ~/embedding_log.txt
