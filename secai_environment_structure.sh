#!/bin/bash
# secAI EC2 Instance Environment Structure Diagnostic Script
# Run this on the EC2 instance to capture the complete environment setup
# Usage: bash secai_environment_structure.sh > secai_diagnostics.txt

echo "=========================================="
echo "secAI EC2 Instance Environment Diagnostics"
echo "Timestamp: $(date)"
echo "=========================================="
echo ""

echo "=========================================="
echo "1. SYSTEM INFORMATION"
echo "=========================================="
echo "Hostname:"
hostname
echo ""
echo "OS Version:"
cat /etc/os-release | grep -E "PRETTY_NAME|VERSION"
echo ""
echo "Kernel:"
uname -a
echo ""
echo "CPU Info:"
lscpu | grep -E "Model name|CPU\(s\)|Thread|Core"
echo ""
echo "Memory:"
free -h
echo ""
echo "Disk Usage:"
df -h
echo ""

echo "=========================================="
echo "2. DOCKER CONTAINERS"
echo "=========================================="
echo "Running Containers:"
docker ps
echo ""
echo "All Containers (including stopped):"
docker ps -a
echo ""
echo "Docker System Info:"
docker system df
echo ""

echo "=========================================="
echo "3. DOCKER CONTAINER DETAILS"
echo "=========================================="
echo "Checking for ChromaDB container..."
CHROMADB_CONTAINER=$(docker ps -a --filter "name=chroma" --format "{{.Names}}" | head -1)
if [ ! -z "$CHROMADB_CONTAINER" ]; then
    echo "ChromaDB Container: $CHROMADB_CONTAINER"
    echo "Status:"
    docker ps -a --filter "name=$CHROMADB_CONTAINER"
    echo ""
    echo "Port Mappings:"
    docker port "$CHROMADB_CONTAINER" 2>/dev/null || echo "No port mappings or container not running"
    echo ""
    echo "Mounts:"
    docker inspect -f '{{ .Mounts }}' "$CHROMADB_CONTAINER" 2>/dev/null || echo "Cannot inspect mounts"
    echo ""
else
    echo "No ChromaDB container found"
fi
echo ""

echo "Checking for Open WebUI container..."
WEBUI_CONTAINER=$(docker ps -a --filter "name=webui\|open-webui" --format "{{.Names}}" | head -1)
if [ ! -z "$WEBUI_CONTAINER" ]; then
    echo "Open WebUI Container: $WEBUI_CONTAINER"
    echo "Status:"
    docker ps -a --filter "name=$WEBUI_CONTAINER"
    echo ""
    echo "Port Mappings:"
    docker port "$WEBUI_CONTAINER" 2>/dev/null || echo "No port mappings or container not running"
    echo ""
    echo "Mounts:"
    docker inspect -f '{{ .Mounts }}' "$WEBUI_CONTAINER" 2>/dev/null || echo "Cannot inspect mounts"
    echo ""
else
    echo "No Open WebUI container found"
fi
echo ""

echo "=========================================="
echo "4. OLLAMA (Native Installation)"
echo "=========================================="
echo "Ollama Service Status:"
systemctl status ollama --no-pager 2>/dev/null || echo "Ollama not running as systemd service"
echo ""
echo "Ollama Process:"
ps aux | grep ollama | grep -v grep || echo "No Ollama process found"
echo ""
echo "Ollama Version:"
ollama --version 2>/dev/null || echo "Ollama command not found"
echo ""
echo "Ollama Models:"
ollama list 2>/dev/null || echo "Cannot list Ollama models"
echo ""
echo "Ollama Model Storage:"
if [ -d ~/.ollama ]; then
    echo "~/.ollama directory:"
    ls -lah ~/.ollama/
    echo ""
    echo "Model sizes:"
    du -sh ~/.ollama/models/* 2>/dev/null || echo "No models found"
else
    echo "~/.ollama directory not found"
fi
echo ""

echo "=========================================="
echo "5. FILESYSTEM STRUCTURE"
echo "=========================================="
echo "/app/data/ Structure:"
if [ -d /app/data ]; then
    ls -lah /app/data/
    echo ""
    echo "Directory sizes:"
    du -sh /app/data/* 2>/dev/null || echo "No subdirectories in /app/data/"
    echo ""
    if [ -d /app/data/edgar ]; then
        echo "/app/data/edgar/ contents:"
        ls -lah /app/data/edgar/ | head -20
        echo ""
    fi
    if [ -d /app/data/processed ]; then
        echo "/app/data/processed/ contents:"
        ls -lah /app/data/processed/ | head -20
        echo ""
    fi
    if [ -d /app/data/embeddings ]; then
        echo "/app/data/embeddings/ contents:"
        ls -lah /app/data/embeddings/ | head -20
        echo ""
    fi
else
    echo "/app/data/ directory not found"
fi
echo ""

echo "Home directory structure:"
ls -lah ~/
echo ""

echo "=========================================="
echo "6. NETWORK & PORTS"
echo "=========================================="
echo "Listening Ports:"
sudo netstat -tlnp 2>/dev/null || sudo ss -tlnp
echo ""
echo "Port 8000 (ChromaDB):"
sudo lsof -i :8000 2>/dev/null || echo "Port 8000 not in use"
echo ""
echo "Port 8080 (Open WebUI):"
sudo lsof -i :8080 2>/dev/null || echo "Port 8080 not in use"
echo ""
echo "Port 11434 (Ollama):"
sudo lsof -i :11434 2>/dev/null || echo "Port 11434 not in use"
echo ""

echo "=========================================="
echo "7. DOCKER COMPOSE (if present)"
echo "=========================================="
for dir in /app /home/ubuntu ~/edgar_anomaly_detection; do
    if [ -f "$dir/docker-compose.yml" ]; then
        echo "Found docker-compose.yml in $dir"
        echo "Content:"
        cat "$dir/docker-compose.yml"
        echo ""
        echo "Docker Compose status:"
        cd "$dir" && docker-compose ps 2>/dev/null
        echo ""
    fi
done
echo ""

echo "=========================================="
echo "8. PYTHON ENVIRONMENT"
echo "=========================================="
echo "Python Version:"
python3 --version 2>/dev/null || echo "Python3 not found"
echo ""
echo "Python Virtual Environments:"
find /app /home/ubuntu -maxdepth 3 -name "venv" -o -name ".venv" 2>/dev/null
echo ""
echo "Pip packages (if venv active):"
if [ ! -z "$VIRTUAL_ENV" ]; then
    echo "Active venv: $VIRTUAL_ENV"
    pip list
else
    echo "No virtual environment currently active"
fi
echo ""

echo "=========================================="
echo "9. GPU INFORMATION (NVIDIA L4)"
echo "=========================================="
echo "NVIDIA SMI:"
nvidia-smi 2>/dev/null || echo "nvidia-smi not available (GPU drivers may not be installed)"
echo ""
echo "CUDA Version:"
nvcc --version 2>/dev/null || echo "CUDA not found"
echo ""

echo "=========================================="
echo "10. RUNNING PROCESSES (Top 20 by Memory)"
echo "=========================================="
ps aux --sort=-%mem | head -20
echo ""

echo "=========================================="
echo "Diagnostics Complete"
echo "Timestamp: $(date)"
echo "=========================================="
