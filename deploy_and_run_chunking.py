"""
Deploy Docker-based chunking pipeline to EC2 and run 2024 Q1 processing

This script will:
1. Upload necessary files to EC2 (Dockerfile, docker-compose.yml, src/, requirements.txt)
2. Build the Docker image on EC2
3. Run the chunking container
4. Monitor progress and show results

Usage: python deploy_and_run_chunking.py
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# EC2 instance details
EC2_HOST = "35.175.134.36"
EC2_USER = "kabe"
SSH_KEY = r"C:\Users\kabec\.ssh\sec_ai_key"

def run_ssh_command(command, timeout=300, show_output=False):
    """Run a command on EC2 via SSH."""
    ssh_cmd = ["ssh", "-i", SSH_KEY, f"{EC2_USER}@{EC2_HOST}", command]

    try:
        if show_output:
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            for line in process.stdout:
                print(line, end='')

            process.wait()
            return process.returncode == 0
        else:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout, encoding='utf-8', errors='replace')
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def main():
    print("=" * 80)
    print("Docker-based 2024 Q1 Chunking Deployment")
    print(f"Host: {EC2_USER}@{EC2_HOST}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Step 1: Test connection
    print_section("STEP 1: Testing Connection")
    test = run_ssh_command("echo 'Connected'")
    if "Error" in test:
        print(f"[FAIL] Cannot connect: {test}")
        sys.exit(1)
    print("[OK] SSH connection successful")

    # Step 2: Create project directory on EC2
    print_section("STEP 2: Setting Up Project Directory")
    project_dir = "/app/home/kabe/edgar_anomaly_detection"

    print(f"Creating {project_dir}...")
    run_ssh_command(f"mkdir -p {project_dir}/src/data {project_dir}/src/models {project_dir}/src/pipeline")

    # Step 3: Upload files via rsync (if available) or scp
    print_section("STEP 3: Uploading Project Files")

    files_to_upload = [
        ("requirements.txt", f"{project_dir}/"),
        ("docker-compose.chunking.yml", f"{project_dir}/"),
        ("src/Dockerfile", f"{project_dir}/src/"),
        ("src/__init__.py", f"{project_dir}/src/"),
        ("src/data/__init__.py", f"{project_dir}/src/data/"),
        ("src/data/text_processor.py", f"{project_dir}/src/data/"),
    ]

    print("Uploading files via SCP...")
    for local_file, remote_path in files_to_upload:
        if not Path(local_file).exists():
            print(f"[SKIP] {local_file} not found")
            continue

        scp_cmd = [
            "scp", "-i", SSH_KEY,
            local_file,
            f"{EC2_USER}@{EC2_HOST}:{remote_path}"
        ]

        try:
            result = subprocess.run(scp_cmd, capture_output=True, timeout=30)
            if result.returncode == 0:
                print(f"[OK] {local_file}")
            else:
                print(f"[FAIL] {local_file}: {result.stderr.decode()}")
        except Exception as e:
            print(f"[FAIL] {local_file}: {e}")

    # Step 4: Verify Docker is installed
    print_section("STEP 4: Verifying Docker Installation")
    docker_check = run_ssh_command("docker --version")
    print(docker_check)

    docker_compose_check = run_ssh_command("docker-compose --version || docker compose version")
    print(docker_compose_check)

    # Step 5: Build Docker image
    print_section("STEP 5: Building Docker Image")
    print("This may take 3-5 minutes (installing dependencies)...\n")

    build_success = run_ssh_command(
        f"cd {project_dir} && docker build -t edgar-chunking -f src/Dockerfile .",
        timeout=600,
        show_output=True
    )

    if not build_success:
        print("\n[FAIL] Docker build failed")
        sys.exit(1)

    print("\n[OK] Docker image built successfully")

    # Step 6: Create output directory
    print_section("STEP 6: Preparing Output Directory")
    run_ssh_command("mkdir -p /app/data/processed/2024/QTR1")
    print("[OK] Output directory ready: /app/data/processed/2024/QTR1")

    # Step 7: Run chunking container
    print_section("STEP 7: Running Chunking Container")
    print("Processing 2024 Q1 (~6,337 files)...")
    print("Estimated time: 10-15 minutes\n")

    start_time = time.time()

    # Run with docker-compose
    run_success = run_ssh_command(
        f"cd {project_dir} && docker-compose -f docker-compose.chunking.yml run --rm chunking",
        timeout=1800,
        show_output=True
    )

    elapsed = time.time() - start_time

    if not run_success:
        print(f"\n[WARN] Container exited with errors (check output above)")
    else:
        print(f"\n[OK] Processing completed in {elapsed/60:.1f} minutes")

    # Step 8: Verify output
    print_section("STEP 8: Verifying Output")

    file_count = run_ssh_command("find /app/data/processed/2024/QTR1/ -name '*.json' | wc -l")
    print(f"JSON files created: {file_count.strip()}")

    dir_size = run_ssh_command("du -sh /app/data/processed/2024/QTR1/")
    print(f"Output size: {dir_size.strip()}")

    # Sample output
    print("\nSample output file (first 40 lines):")
    sample = run_ssh_command("find /app/data/processed/2024/QTR1/ -name '*.json' 2>/dev/null | head -1 | xargs head -40 2>/dev/null || echo 'No files found'")
    print(sample)

    # Step 9: Cleanup
    print_section("STEP 9: Cleanup (Optional)")
    print("Docker image remains on EC2 for future use")
    print(f"To remove: ssh and run 'docker rmi edgar-chunking'")

    print_section("DEPLOYMENT COMPLETE")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Output: /app/data/processed/2024/QTR1/")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
