"""
Generate chunk comparison HTML from actual processed data
NO conclusions - just shows you the chunks so YOU can evaluate
"""

import json
from pathlib import Path

def generate_comparison_html(filing_idx=0, chunk_pct=0.4):
    """
    Generate HTML comparing the same chunk across different sizes

    Args:
        filing_idx: Which filing to use (0-1374)
        chunk_pct: Which percentage through the document (0.0-1.0)
                   e.g., 0.4 = 40% through the document
    """

    # Load data for different chunk sizes
    sizes_to_compare = [200, 500, 1000, 2000]
    chunks_by_size = {}

    print(f"[INFO] Loading chunks from filing {filing_idx} at ~{chunk_pct*100:.0f}% through document...\n")

    for size in sizes_to_compare:
        file_path = Path(f'output/processed_samples_{size}tok.json')

        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if filing_idx >= len(data):
            print(f"[ERROR] Filing index {filing_idx} out of range (max: {len(data)-1})")
            return

        filing = data[filing_idx]

        # Calculate chunk index based on percentage through document
        actual_chunk_idx = int(chunk_pct * filing['num_chunks'])
        # Ensure it's within bounds
        actual_chunk_idx = min(actual_chunk_idx, filing['num_chunks'] - 1)
        actual_chunk_idx = max(0, actual_chunk_idx)

        print(f"  {size:>4} tokens: chunk {actual_chunk_idx+1}/{filing['num_chunks']} (~{100*actual_chunk_idx/filing['num_chunks']:.0f}% through)")

        chunk = filing['chunks'][actual_chunk_idx]

        # Extract content (skip header)
        text = chunk['text']
        lines = text.split('\n')
        content = '\n'.join(lines[2:]) if len(lines) > 2 else text

        chunks_by_size[size] = {
            'content': content,
            'metadata': filing['metadata'],
            'chunk_index': actual_chunk_idx,
            'total_chunks': filing['num_chunks'],
            'total_tokens': filing['total_tokens'],
            'file_name': filing['file_name']
        }

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Chunk Size Comparison - Real Data</title>
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
        .instructions {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
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
        .chunk-container {{
            background: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chunk-header {{
            background: #3498db;
            color: white;
            padding: 15px;
            margin: -20px -20px 15px -20px;
            border-radius: 5px 5px 0 0;
            font-weight: bold;
            font-size: 18px;
        }}
        .content {{
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.6;
            font-size: 13px;
            background: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #3498db;
            max-height: 400px;
            overflow-y: auto;
        }}
        .stats {{
            color: #7f8c8d;
            font-size: 13px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #ecf0f1;
        }}
        .evaluation-section {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
        }}
        textarea {{
            width: 100%;
            min-height: 80px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }}
        .eval-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        button {{
            padding: 8px 16px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn-good {{
            background: #4caf50;
            color: white;
        }}
        .btn-fragmented {{
            background: #ff9800;
            color: white;
        }}
        .btn-broad {{
            background: #f44336;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Chunk Size Comparison - Actual Data</h1>
        <p>Review the SAME content at different chunk sizes and decide which works best</p>
    </div>

    <div class="instructions">
        <h3>📋 Instructions:</h3>
        <ol>
            <li><strong>Read each chunk below</strong> (same content, different sizes)</li>
            <li><strong>For EACH chunk, ask yourself:</strong>
                <ul>
                    <li>✅ <strong>Is it COMPLETE?</strong> Does it contain a full thought/section?</li>
                    <li>✅ <strong>Is it COHERENT?</strong> Can you understand it standalone?</li>
                    <li>❌ <strong>Is it FRAGMENTED?</strong> Cut off mid-sentence? Missing context?</li>
                    <li>❌ <strong>Is it TOO BROAD?</strong> Mixing unrelated topics?</li>
                </ul>
            </li>
            <li><strong>Write notes</strong> in the text box below each chunk</li>
            <li><strong>Compare your notes</strong> across all sizes at the end</li>
        </ol>
        <p><strong>⚠️ NO PRE-DETERMINED ANSWER:</strong> YOU decide which size works best based on what you see!</p>
    </div>

    <div class="filing-info">
        <strong>📄 Filing:</strong> {chunks_by_size[200]['metadata'].get('COMPANY_NAME', 'Unknown')}<br>
        <strong>📋 Form Type:</strong> {chunks_by_size[200]['metadata'].get('FORM_TYPE', 'Unknown')}<br>
        <strong>📅 Filing Date:</strong> {chunks_by_size[200]['metadata'].get('FILING_DATE', 'Unknown')}<br>
        <strong>🆔 CIK:</strong> {chunks_by_size[200]['metadata'].get('CIK', 'Unknown')}<br>
        <strong>📁 File:</strong> {chunks_by_size[200]['file_name']}<br>
        <strong>📍 Document Position:</strong> ~{chunk_pct*100:.0f}% through filing (comparing same location across sizes)
    </div>
"""

    # Add each chunk size
    for size in sizes_to_compare:
        data = chunks_by_size[size]
        word_count = len(data['content'].split())
        char_count = len(data['content'])

        html += f"""
    <div class="chunk-container">
        <div class="chunk-header">🔹 {size} TOKENS</div>
        <div class="content">{data['content'][:3000]}{"..." if len(data['content']) > 3000 else ""}</div>
        <div class="stats">
            📏 <strong>Size:</strong> {size} tokens (~{word_count} words, {char_count:,} characters)<br>
            📊 <strong>Chunk:</strong> {data['chunk_index'] + 1} of {data['total_chunks']}<br>
            📈 <strong>Filing total:</strong> {data['total_tokens']:,} tokens
        </div>
    </div>
"""

    html += """
    <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; margin-top: 30px;">
        <h2>🎯 Summary - Which Size Works Best?</h2>
        <textarea id="final_summary" placeholder="After reviewing all 4 sizes, write your conclusion here:&#10;&#10;- Which size felt most complete and coherent?&#10;- Which was too fragmented?&#10;- Which was too broad?&#10;- Your recommended chunk size:&#10;- Why?" style="min-height: 150px;"></textarea>
        <p style="margin-top: 15px; color: #666;">
            <strong>Note:</strong> Your evaluation is based on ONE chunk. You should review 3-5 different chunks
            from different filings to validate your conclusion!
        </p>
    </div>

    <div style="background: #e3f2fd; padding: 20px; border-radius: 5px; margin-top: 20px;">
        <h3>📚 Reference: What to Look For</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f5f5f5;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Criteria</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Good Chunk</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Bad Chunk</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Completeness</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">Contains full idea/section</td>
                <td style="padding: 10px; border: 1px solid #ddd;">Sentences cut off mid-thought</td>
            </tr>
            <tr style="background: #f9f9f9;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Coherence</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">One topic, understandable standalone</td>
                <td style="padding: 10px; border: 1px solid #ddd;">Mixes unrelated topics</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Context</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">Enough info to understand meaning</td>
                <td style="padding: 10px; border: 1px solid #ddd;">Missing crucial context</td>
            </tr>
            <tr style="background: #f9f9f9;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Focus</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">Targeted, little irrelevant content</td>
                <td style="padding: 10px; border: 1px solid #ddd;">Lots of noise, unrelated info</td>
            </tr>
        </table>
    </div>
</body>
</html>
"""

    # Save HTML
    output_path = Path('chunk_comparison_real_data.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] Generated: {output_path.absolute()}")
    print(f"\n[INFO] Open this file in your browser to review chunks")
    print(f"[INFO] Write your evaluation in the text boxes")
    print(f"[INFO] NO pre-determined conclusions - YOU decide!")

    return output_path


if __name__ == '__main__':
    print("="*80)
    print("CHUNK COMPARISON GENERATOR")
    print("="*80)
    print("\nThis generates an HTML file with REAL chunks from your data")
    print("so YOU can evaluate which size works best.\n")

    filing_idx = input("Enter filing index (0-1374, try 50 for a 90s filing): ").strip()
    filing_idx = int(filing_idx) if filing_idx else 50

    chunk_pct_input = input("Enter position percentage (0-100, try 40 for middle): ").strip()
    chunk_pct = float(chunk_pct_input) / 100 if chunk_pct_input else 0.4

    output_path = generate_comparison_html(filing_idx, chunk_pct)

    print(f"\n[NEXT] Open: {output_path}")
    print("[NEXT] Review each chunk and write your notes")
    print("[NEXT] Run this script again with different filing/position to validate!")
