"""
Run diagnostics on secAI EC2 instance remotely via SSH
Usage: python secai_remote_diagnostics.py > secai_ec2_diagnostics.txt
"""

import subprocess
import sys
from datetime import datetime

# EC2 instance details
EC2_HOST = "35.175.134.36"
EC2_USER = "ubuntu"
SSH_KEY = None  # Set this if you have a specific key path, e.g., "~/.ssh/secai.pem"

def run_ssh_command(command):
    """Run a command on EC2 via SSH."""
    ssh_cmd = ["ssh"]

    if SSH_KEY:
        ssh_cmd.extend(["-i", SSH_KEY])

    ssh_cmd.append(f"{EC2_USER}@{EC2_HOST}")
    ssh_cmd.append(command)

    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def main():
    print("=" * 60)
    print("secAI EC2 Instance Remote Diagnostics")
    print(f"Host: {EC2_USER}@{EC2_HOST}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Test SSH connection
    print("\nTesting SSH connection...")
    test = run_ssh_command("echo 'SSH connection successful'")
    if "Error" in test or "timed out" in test:
        print(f"\n[FAIL] Cannot connect to EC2 instance: {test}")
        print("\nTroubleshooting:")
        print("1. Ensure you can SSH manually: ssh ubuntu@35.175.134.36")
        print("2. Check if SSH key is configured in ~/.ssh/config")
        print("3. If using a specific key, update SSH_KEY variable in this script")
        sys.exit(1)
    print(test)

    # System Information
    print_section("1. SYSTEM INFORMATION")
    print("Hostname:")
    print(run_ssh_command("hostname"))
    print("\nOS Version:")
    print(run_ssh_command("cat /etc/os-release | grep -E 'PRETTY_NAME|VERSION'"))
    print("\nKernel:")
    print(run_ssh_command("uname -a"))
    print("\nCPU Info:")
    print(run_ssh_command("lscpu | grep -E 'Model name|CPU\\(s\\)|Thread|Core'"))
    print("\nMemory:")
    print(run_ssh_command("free -h"))
    print("\nDisk Usage:")
    print(run_ssh_command("df -h"))

    # Docker Containers
    print_section("2. DOCKER CONTAINERS")
    print("Running Containers:")
    print(run_ssh_command("docker ps"))
    print("\nAll Containers:")
    print(run_ssh_command("docker ps -a"))
    print("\nDocker System Usage:")
    print(run_ssh_command("docker system df"))

    # ChromaDB Container
    print_section("3. CHROMADB CONTAINER")
    print("Finding ChromaDB container...")
    chromadb_name = run_ssh_command("docker ps -a --filter 'name=chroma' --format '{{.Names}}' | head -1")
    if chromadb_name and "Error" not in chromadb_name and chromadb_name.strip():
        print(f"ChromaDB Container: {chromadb_name}")
        print("\nStatus:")
        print(run_ssh_command(f"docker ps -a --filter 'name={chromadb_name.strip()}'"))
        print("\nPort Mappings:")
        print(run_ssh_command(f"docker port {chromadb_name.strip()}"))
        print("\nLogs (last 20 lines):")
        print(run_ssh_command(f"docker logs {chromadb_name.strip()} --tail 20"))
    else:
        print("No ChromaDB container found")

    # Open WebUI Container
    print_section("4. OPEN WEBUI CONTAINER")
    print("Finding Open WebUI container...")
    webui_name = run_ssh_command("docker ps -a --filter 'name=webui' --format '{{.Names}}' | head -1")
    if not webui_name.strip() or "Error" in webui_name:
        webui_name = run_ssh_command("docker ps -a --filter 'name=open-webui' --format '{{.Names}}' | head -1")

    if webui_name and "Error" not in webui_name and webui_name.strip():
        print(f"Open WebUI Container: {webui_name}")
        print("\nStatus:")
        print(run_ssh_command(f"docker ps -a --filter 'name={webui_name.strip()}'"))
        print("\nPort Mappings:")
        print(run_ssh_command(f"docker port {webui_name.strip()}"))
        print("\nLogs (last 20 lines):")
        print(run_ssh_command(f"docker logs {webui_name.strip()} --tail 20"))
    else:
        print("No Open WebUI container found")

    # Ollama
    print_section("5. OLLAMA (Native Installation)")
    print("Ollama Service Status:")
    print(run_ssh_command("systemctl status ollama --no-pager 2>/dev/null || echo 'Not running as systemd service'"))
    print("\nOllama Process:")
    print(run_ssh_command("ps aux | grep ollama | grep -v grep || echo 'No Ollama process found'"))
    print("\nOllama Version:")
    print(run_ssh_command("ollama --version"))
    print("\nOllama Models:")
    print(run_ssh_command("ollama list"))
    print("\nOllama Storage:")
    print(run_ssh_command("du -sh ~/.ollama/ 2>/dev/null || echo 'Ollama directory not found'"))
    print(run_ssh_command("du -sh ~/.ollama/models/* 2>/dev/null || echo 'No models found'"))

    # Filesystem
    print_section("6. FILESYSTEM STRUCTURE")
    print("/app/data/ Directory:")
    print(run_ssh_command("ls -lah /app/data/ 2>/dev/null || echo '/app/data/ not found'"))
    print("\nDirectory Sizes:")
    print(run_ssh_command("du -sh /app/data/* 2>/dev/null || echo 'No subdirectories'"))
    print("\n/app/data/edgar/ Contents (first 20):")
    print(run_ssh_command("ls -lah /app/data/edgar/ 2>/dev/null | head -20 || echo 'Directory not found'"))
    print("\n/app/data/processed/ Contents:")
    print(run_ssh_command("ls -lah /app/data/processed/ 2>/dev/null || echo 'Directory not found'"))
    print("\n/app/data/embeddings/ Contents:")
    print(run_ssh_command("ls -lah /app/data/embeddings/ 2>/dev/null || echo 'Directory not found'"))

    # Network & Ports
    print_section("7. NETWORK & PORTS")
    print("Listening Ports:")
    print(run_ssh_command("sudo netstat -tlnp 2>/dev/null || sudo ss -tlnp"))
    print("\nPort 8000 (ChromaDB):")
    print(run_ssh_command("sudo lsof -i :8000 2>/dev/null || echo 'Port 8000 not in use'"))
    print("\nPort 8080 (Open WebUI):")
    print(run_ssh_command("sudo lsof -i :8080 2>/dev/null || echo 'Port 8080 not in use'"))
    print("\nPort 11434 (Ollama):")
    print(run_ssh_command("sudo lsof -i :11434 2>/dev/null || echo 'Port 11434 not in use'"))

    # Docker Compose
    print_section("8. DOCKER COMPOSE")
    print("Checking for docker-compose.yml files:")
    print(run_ssh_command("find /app /home/ubuntu -maxdepth 2 -name 'docker-compose.yml' 2>/dev/null || echo 'No docker-compose.yml found'"))

    # GPU
    print_section("9. GPU (NVIDIA L4)")
    print("NVIDIA SMI:")
    print(run_ssh_command("nvidia-smi 2>/dev/null || echo 'nvidia-smi not available'"))
    print("\nCUDA Version:")
    print(run_ssh_command("nvcc --version 2>/dev/null || echo 'CUDA not found'"))

    # Top Processes
    print_section("10. RUNNING PROCESSES (Top 15 by Memory)")
    print(run_ssh_command("ps aux --sort=-%mem | head -15"))

    print("\n" + "=" * 60)
    print("Remote Diagnostics Complete")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
