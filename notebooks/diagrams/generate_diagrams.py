"""
Generate PNG diagrams from mermaid files using mermaid.ink API.

Usage:
    python generate_diagrams.py
"""

import base64
import requests
from pathlib import Path

def mermaid_to_png(mermaid_file: Path, output_file: Path):
    """Convert mermaid file to PNG using mermaid.ink API."""

    # Read mermaid code
    with open(mermaid_file, 'r', encoding='utf-8') as f:
        mermaid_code = f.read()

    # Create JSON payload for kroki.io (alternative to mermaid.ink)
    # Use kroki.io which is more reliable
    import json
    import zlib

    # Compress and encode
    compressed = zlib.compress(mermaid_code.encode('utf-8'), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')

    # Use kroki.io API
    url = f"https://kroki.io/mermaid/png/{encoded}"

    print(f"Generating {output_file.name}...")
    response = requests.get(url)

    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"[OK] Created {output_file.name}")
    else:
        print(f"[FAIL] Failed to generate {output_file.name}: {response.status_code}")

def main():
    diagrams_dir = Path(__file__).parent

    # Define mermaid files and their output names
    diagrams = [
        ('architecture.mmd', 'architecture.png'),
        ('raptor_pipeline.mmd', 'raptor_pipeline.png'),
        ('data_processing_workflow.mmd', 'data_processing_workflow.png'),
    ]

    for mmd_file, png_file in diagrams:
        mermaid_path = diagrams_dir / mmd_file
        output_path = diagrams_dir / png_file

        if mermaid_path.exists():
            mermaid_to_png(mermaid_path, output_path)
        else:
            print(f"[WARN] {mmd_file} not found")

if __name__ == '__main__':
    main()
