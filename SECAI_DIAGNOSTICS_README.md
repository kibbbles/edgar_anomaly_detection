# secAI EC2 Instance Diagnostics

## Quick Start

### Activate Python Virtual Environment (Local)

**On Windows:**
```bash
.venv\Scripts\activate
```

**On Linux/Mac:**
```bash
source .venv/bin/activate
```

**On EC2 (if venv is set up there):**
```bash
source /app/.venv/bin/activate
# Or wherever the venv is located
```

---

## Running Diagnostics on secAI EC2 Instance

### 1. Connect to the EC2 Instance
```bash
ssh -i /path/to/your-key.pem ubuntu@35.175.134.36
```

### 2. Upload the Diagnostic Script
From your local machine:
```bash
scp -i /path/to/your-key.pem secai_environment_structure.sh ubuntu@35.175.134.36:~/
```

Or, if already connected to EC2, create it directly:
```bash
nano secai_environment_structure.sh
# Paste the script content, then Ctrl+X, Y, Enter
```

### 3. Run the Diagnostic Script
```bash
# Make it executable
chmod +x secai_environment_structure.sh

# Run and save output to file
bash secai_environment_structure.sh > secai_diagnostics.txt

# View the output
cat secai_diagnostics.txt

# Or view with pagination
less secai_diagnostics.txt
```

### 4. Download the Diagnostics File
From your local machine:
```bash
scp -i /path/to/your-key.pem ubuntu@35.175.134.36:~/secai_diagnostics.txt .
```

---

## What the Script Checks

1. **System Information** - OS, CPU, memory, disk
2. **Docker Containers** - Running and stopped containers
3. **Container Details** - ChromaDB and Open WebUI specifics
4. **Ollama Installation** - Service status, models, storage
5. **Filesystem Structure** - /app/data/ directory tree
6. **Network & Ports** - Listening ports (8000, 8080, 11434)
7. **Docker Compose** - Configuration files if present
8. **Python Environment** - Python version, venvs, packages
9. **GPU Information** - NVIDIA L4, CUDA availability
10. **Running Processes** - Top memory consumers

---

## Quick Manual Checks (Without Script)

If you just want to quickly check specific things:

### Docker Containers
```bash
docker ps -a
```

### ChromaDB Container
```bash
docker ps | grep chroma
docker logs <chromadb_container_name>
```

### Open WebUI Container
```bash
docker ps | grep webui
docker logs <webui_container_name>
```

### Ollama
```bash
ollama list
systemctl status ollama
```

### Data Directory
```bash
ls -lah /app/data/
du -sh /app/data/*
```

### Ports
```bash
sudo lsof -i :8000  # ChromaDB
sudo lsof -i :8080  # Open WebUI
sudo lsof -i :11434 # Ollama
```

---

## Troubleshooting

### If ChromaDB isn't running:
```bash
# Start the container (if it exists but is stopped)
docker start <chromadb_container_name>

# Check logs for errors
docker logs <chromadb_container_name>
```

### If Open WebUI isn't accessible:
```bash
# Check if it's running
docker ps | grep webui

# Check port mapping
docker port <webui_container_name>

# Check logs
docker logs <webui_container_name>
```

### If Ollama isn't responding:
```bash
# Check if the service is running
systemctl status ollama

# Restart Ollama
sudo systemctl restart ollama

# Check if models are loaded
ollama list
```

---

## Expected Structure

Based on your setup, you should see:

### Docker Containers
- **ChromaDB**: Running on port 8000
- **Open WebUI**: Running on port 8080

### Ollama (Native)
- Service running (not in Docker)
- Models stored in `~/.ollama/`
- Listening on port 11434

### Filesystem
```
/app/data/
├── edgar/              # Raw SEC filing ZIPs + extracted files
├── processed/          # Chunked filing JSON files
└── embeddings/         # Vector embeddings (NPY files)
```

---

## Notes

- The script requires sudo for some commands (port checking)
- GPU information requires NVIDIA drivers to be installed
- Some paths may vary depending on your actual setup
- The script is safe to run - it only reads information, doesn't modify anything
