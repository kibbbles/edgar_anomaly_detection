"""
Generate chunk comparison HTML with multiple positions (beginning, middle, end)
Shows you chunks from different parts of the filing for better evaluation
"""

import json
from pathlib import Path


def generate_multi_position_html(filing_idx=0, positions=[0.2, 0.5, 0.8]):
    """
    Generate HTML comparing chunks at multiple positions through the document

    Args:
        filing_idx: Which filing to use (0-1374)
        positions: List of percentages (0.0-1.0) to compare
                   Default: [0.2, 0.5, 0.8] = beginning, middle, end
    """

    sizes_to_compare = [200, 500, 1000, 2000]

    # Load metadata from first size
    first_size = sizes_to_compare[0]
    file_path = Path(f'output/processed_samples_{first_size}tok.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if filing_idx >= len(data):
        print(f"[ERROR] Filing index {filing_idx} out of range (max: {len(data)-1})")
        return

    filing_metadata = data[filing_idx]['metadata']
    filing_name = data[filing_idx]['file_name']

    print(f"[INFO] Generating comparison for filing {filing_idx}")
    print(f"       {filing_metadata.get('COMPANY_NAME', 'Unknown')}")
    print(f"       Positions: {', '.join([f'{p*100:.0f}%' for p in positions])}\n")

    # Start HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Multi-Position Chunk Comparison</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .filing-info {{
            background: #e3f2fd;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            border-left: 4px solid #2196f3;
        }}
        .position-section {{
            background: #fff;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .position-header {{
            background: #9c27b0;
            color: white;
            padding: 15px;
            margin: -20px -20px 20px -20px;
            border-radius: 5px 5px 0 0;
            font-size: 20px;
            font-weight: bold;
        }}
        .chunk-container {{
            background: #fafafa;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .chunk-header {{
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            color: #3498db;
        }}
        .content {{
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.6;
            font-size: 13px;
            background: #fff;
            padding: 15px;
            border-radius: 3px;
            max-height: 300px;
            overflow-y: auto;
        }}
        .stats {{
            color: #7f8c8d;
            font-size: 12px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Multi-Position Chunk Size Comparison</h1>
        <p>Compare chunk sizes at different positions throughout the filing</p>
    </div>

    <div class="filing-info">
        <strong>📄 Filing:</strong> {filing_metadata.get('COMPANY_NAME', 'Unknown')}<br>
        <strong>📋 Form Type:</strong> {filing_metadata.get('FORM_TYPE', 'Unknown')}<br>
        <strong>📅 Filing Date:</strong> {filing_metadata.get('FILING_DATE', 'Unknown')}<br>
        <strong>🆔 CIK:</strong> {filing_metadata.get('CIK', 'Unknown')}<br>
        <strong>📁 File:</strong> {filing_name}
    </div>
"""

    # Generate sections for each position
    for position in positions:
        position_name = {
            0.2: "BEGINNING",
            0.5: "MIDDLE",
            0.8: "END"
        }.get(position, f"{position*100:.0f}%")

        html += f"""
    <div class="position-section">
        <div class="position-header">📍 {position_name} of Filing (~{position*100:.0f}% through)</div>
"""

        # Load chunks for each size at this position
        for size in sizes_to_compare:
            file_path = Path(f'output/processed_samples_{size}tok.json')

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            filing = data[filing_idx]

            # Calculate chunk index based on percentage
            chunk_idx = int(position * filing['num_chunks'])
            chunk_idx = min(chunk_idx, filing['num_chunks'] - 1)
            chunk_idx = max(0, chunk_idx)

            chunk = filing['chunks'][chunk_idx]

            # Extract content (skip header)
            text = chunk['text']
            lines = text.split('\n')
            content = '\n'.join(lines[2:]) if len(lines) > 2 else text

            word_count = len(content.split())
            char_count = len(content)

            # Truncate if too long
            display_content = content[:2000] + "..." if len(content) > 2000 else content

            html += f"""
        <div class="chunk-container">
            <div class="chunk-header">🔹 {size} TOKENS</div>
            <div class="content">{display_content}</div>
            <div class="stats">
                📏 {size} tokens (~{word_count} words, {char_count:,} characters) |
                📊 Chunk {chunk_idx + 1}/{filing['num_chunks']}
            </div>
        </div>
"""

        html += """
    </div>
"""

    html += """
</body>
</html>
"""

    # Save HTML
    output_path = Path('chunk_comparison_multi_position.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Generated: {output_path.absolute()}")
    print(f"\n[INFO] Open this file in your browser to review chunks")
    print(f"[INFO] Compare how each size handles different parts of the filing")

    return output_path


if __name__ == '__main__':
    print("="*80)
    print("MULTI-POSITION CHUNK COMPARISON GENERATOR")
    print("="*80)
    print("\nThis generates comparisons at BEGINNING, MIDDLE, and END of filing")
    print("so you can evaluate chunk quality across different content types.\n")

    filing_idx = input("Enter filing index (0-1374, try 50 for a 90s filing): ").strip()
    filing_idx = int(filing_idx) if filing_idx else 50

    output_path = generate_multi_position_html(filing_idx, positions=[0.2, 0.5, 0.8])

    print(f"\n[NEXT] Open: {output_path}")
    print("[NEXT] Look at how each chunk size handles:")
    print("         - BEGINNING (20%): Often contains business overview")
    print("         - MIDDLE (50%): Usually financial statements/tables")
    print("         - END (80%): Typically signatures/exhibits")
