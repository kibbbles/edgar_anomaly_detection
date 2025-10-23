"""
secAI Environment Structure Diagnostic Script
Run locally to capture environment diagnostics for both local and remote EC2 setup
Usage: python secai_environment_structure.py > secai_diagnostics.txt
"""

import subprocess
import platform
import os
import sys
from pathlib import Path
from datetime import datetime
import shutil

def run_command(cmd, shell=True):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def check_system_info():
    """Check basic system information."""
    print_section("1. SYSTEM INFORMATION")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Python Version: {sys.version}")
    print(f"Hostname: {platform.node()}")

    # Memory info (Windows-specific)
    if platform.system() == "Windows":
        mem_info = run_command("wmic computersystem get TotalPhysicalMemory")
        print(f"\nMemory Info:\n{mem_info}")

    # Disk info
    try:
        total, used, free = shutil.disk_usage("/")
        print(f"\nDisk Usage:")
        print(f"Total: {total // (2**30)} GB")
        print(f"Used: {used // (2**30)} GB")
        print(f"Free: {free // (2**30)} GB")
    except Exception as e:
        print(f"Disk info error: {e}")

def check_docker():
    """Check Docker installation and containers."""
    print_section("2. DOCKER CONTAINERS (Local)")

    # Check if Docker is installed
    docker_version = run_command("docker --version")
    print(f"Docker Version: {docker_version}")

    # Running containers
    print("\nRunning Containers:")
    print(run_command("docker ps"))

    # All containers
    print("\nAll Containers (including stopped):")
    print(run_command("docker ps -a"))

    # Docker system info
    print("\nDocker System Usage:")
    print(run_command("docker system df"))

def check_docker_details():
    """Check specific Docker container details."""
    print_section("3. DOCKER CONTAINER DETAILS")

    # Check for ChromaDB container
    print("Checking for ChromaDB container...")
    chromadb_check = run_command('docker ps -a --filter "name=chroma" --format "{{.Names}}"')
    if chromadb_check and "Error" not in chromadb_check:
        print(f"ChromaDB Container: {chromadb_check}")
        print("\nStatus:")
        print(run_command(f'docker ps -a --filter "name={chromadb_check}"'))
        print("\nPort Mappings:")
        print(run_command(f'docker port {chromadb_check}'))
        print("\nMounts:")
        print(run_command(f'docker inspect -f "{{{{ .Mounts }}}}" {chromadb_check}'))
    else:
        print("No ChromaDB container found")

    # Check for Open WebUI container
    print("\nChecking for Open WebUI container...")
    webui_check = run_command('docker ps -a --filter "name=webui" --format "{{.Names}}"')
    if not webui_check or "Error" in webui_check:
        webui_check = run_command('docker ps -a --filter "name=open-webui" --format "{{.Names}}"')

    if webui_check and "Error" not in webui_check:
        print(f"Open WebUI Container: {webui_check}")
        print("\nStatus:")
        print(run_command(f'docker ps -a --filter "name={webui_check}"'))
        print("\nPort Mappings:")
        print(run_command(f'docker port {webui_check}'))
        print("\nMounts:")
        print(run_command(f'docker inspect -f "{{{{ .Mounts }}}}" {webui_check}'))
    else:
        print("No Open WebUI container found")

def check_ollama():
    """Check Ollama installation."""
    print_section("4. OLLAMA INSTALLATION")

    # Ollama version
    print("Ollama Version:")
    print(run_command("ollama --version"))

    # Ollama models
    print("\nOllama Models:")
    print(run_command("ollama list"))

    # Ollama process (Windows)
    if platform.system() == "Windows":
        print("\nOllama Process:")
        print(run_command('tasklist | findstr "ollama"'))
    else:
        print("\nOllama Process:")
        print(run_command("ps aux | grep ollama | grep -v grep"))

    # Check Ollama directory
    ollama_home = Path.home() / ".ollama"
    if ollama_home.exists():
        print(f"\nOllama Home Directory ({ollama_home}):")
        for item in ollama_home.iterdir():
            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file()) if item.is_dir() else item.stat().st_size
            size_gb = size / (1024**3)
            print(f"  {item.name}: {size_gb:.2f} GB")
    else:
        print(f"\nOllama directory not found at {ollama_home}")

def check_filesystem():
    """Check local project filesystem structure."""
    print_section("5. LOCAL FILESYSTEM STRUCTURE")

    project_root = Path.cwd()
    print(f"Project Root: {project_root}")

    # Check main directories
    main_dirs = ["data", "notebooks", "src", ".venv"]
    for dirname in main_dirs:
        dir_path = project_root / dirname
        if dir_path.exists():
            if dir_path.is_dir():
                size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                size_mb = size / (1024**2)
                file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
                print(f"\n{dirname}/: {size_mb:.1f} MB ({file_count} files)")

                # Show structure for important directories
                if dirname == "data":
                    print("  Data structure:")
                    for subdir in sorted(dir_path.iterdir()):
                        if subdir.is_dir():
                            sub_size = sum(f.stat().st_size for f in subdir.rglob('*') if f.is_file())
                            sub_size_mb = sub_size / (1024**2)
                            print(f"    {subdir.name}/: {sub_size_mb:.1f} MB")
            else:
                print(f"\n{dirname}: (file, not directory)")
        else:
            print(f"\n{dirname}/: NOT FOUND")

    # List root directory files
    print("\nRoot Directory Files:")
    for item in sorted(project_root.iterdir()):
        if item.is_file():
            size_kb = item.stat().st_size / 1024
            print(f"  {item.name}: {size_kb:.1f} KB")

def check_network():
    """Check network and ports."""
    print_section("6. NETWORK & PORTS (Local)")

    print("Checking listening ports...")

    if platform.system() == "Windows":
        print("\nListening TCP Ports:")
        print(run_command("netstat -an | findstr LISTENING"))

        # Check specific ports
        print("\nPort 8000 (ChromaDB):")
        print(run_command("netstat -an | findstr :8000"))

        print("\nPort 8080 (Open WebUI):")
        print(run_command("netstat -an | findstr :8080"))

        print("\nPort 11434 (Ollama):")
        print(run_command("netstat -an | findstr :11434"))
    else:
        print("\nListening Ports:")
        print(run_command("netstat -tlnp"))

def check_python_env():
    """Check Python environment."""
    print_section("7. PYTHON ENVIRONMENT")

    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print(f"Virtual Environment: {os.environ.get('VIRTUAL_ENV', 'Not active')}")

    # Check if in venv
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"In Virtual Environment: {in_venv}")

    # List installed packages
    print("\nInstalled Packages:")
    print(run_command("pip list"))

    # Check requirements.txt
    req_file = Path.cwd() / "requirements.txt"
    if req_file.exists():
        print("\nrequirements.txt exists")
        with open(req_file, 'r', encoding='utf-8') as f:
            print(f"Requirements count: {len(f.readlines())} packages")
    else:
        print("\nrequirements.txt: NOT FOUND")

def check_git():
    """Check Git status."""
    print_section("8. GIT REPOSITORY")

    print("Git Version:")
    print(run_command("git --version"))

    print("\nGit Status:")
    print(run_command("git status"))

    print("\nCurrent Branch:")
    print(run_command("git branch --show-current"))

    print("\nRecent Commits (last 5):")
    print(run_command('git log --oneline -5'))

    print("\nRemote URL:")
    print(run_command("git remote -v"))

def check_project_files():
    """Check key project files."""
    print_section("9. KEY PROJECT FILES")

    project_root = Path.cwd()
    key_files = [
        "README.md",
        "requirements.txt",
        ".gitignore",
        "CLAUDE.md",
        "docker-compose.yml",
        "docker-compose.dev.yml",
        "docker-compose.prod.yml"
    ]

    for filename in key_files:
        file_path = project_root / filename
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"[OK] {filename}: {size_kb:.1f} KB")
        else:
            print(f"[MISSING] {filename}")

def check_notebooks():
    """Check Jupyter notebooks."""
    print_section("10. JUPYTER NOTEBOOKS")

    notebooks_dir = Path.cwd() / "notebooks"
    if notebooks_dir.exists():
        notebooks = list(notebooks_dir.rglob("*.ipynb"))
        print(f"Total notebooks found: {len(notebooks)}")
        print("\nNotebooks:")
        for nb in sorted(notebooks):
            rel_path = nb.relative_to(Path.cwd())
            size_kb = nb.stat().st_size / 1024
            print(f"  {rel_path}: {size_kb:.1f} KB")
    else:
        print("notebooks/ directory not found")

def main():
    """Run all diagnostic checks."""
    print("=" * 60)
    print("secAI Environment Structure Diagnostics (Local)")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {Path.cwd()}")
    print("=" * 60)

    try:
        check_system_info()
        check_docker()
        check_docker_details()
        check_ollama()
        check_filesystem()
        check_network()
        check_python_env()
        check_git()
        check_project_files()
        check_notebooks()
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during diagnostics: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Diagnostics Complete")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
