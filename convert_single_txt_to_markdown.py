"""
Convert a single SEC .txt file (with embedded HTML) to Markdown
KEEPS SEC-HEADER metadata intact
"""
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import html2text

sys.stdout.reconfigure(encoding='utf-8')

def extract_sec_header(txt_content):
    """Extract SEC header from .txt file"""
    header_start = txt_content.find('<SEC-HEADER>')
    header_end = txt_content.find('</SEC-HEADER>')

    if header_start == -1 or header_end == -1:
        return None

    # Include the tags
    header = txt_content[header_start:header_end + 13]
    return header

def extract_html_from_sec_txt(txt_content):
    """Extract HTML content from SEC .txt file format"""
    # Find HTML between <TEXT> tags
    text_start = txt_content.find('<TEXT>')
    text_end = txt_content.find('</TEXT>')

    if text_start == -1 or text_end == -1:
        print("[ERROR] Could not find <TEXT> tags in file")
        return None

    html_content = txt_content[text_start + 6:text_end].strip()
    return html_content

def convert_txt_to_markdown(txt_file_path, output_md_path):
    """Convert SEC .txt file to Markdown, preserving SEC header"""
    print(f"\n[Processing] {Path(txt_file_path).name}")

    # Read entire file
    with open(txt_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        txt_content = f.read()

    # Extract SEC header
    print("  [Step 1] Extracting SEC-HEADER metadata...")
    sec_header = extract_sec_header(txt_content)

    if sec_header:
        print(f"  [Found] SEC-HEADER ({len(sec_header):,} chars)")
    else:
        print("  [Warning] No SEC-HEADER found")

    # Extract HTML from .txt file
    print("  [Step 2] Extracting HTML from <TEXT> tags...")
    html_content = extract_html_from_sec_txt(txt_content)

    if not html_content:
        return False

    print(f"  [Step 3] Parsing HTML ({len(html_content):,} chars)...")

    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove hidden XBRL metadata
    for hidden in soup.find_all(['ix:hidden', 'ix:header'], recursive=True):
        hidden.decompose()

    # Remove script and style tags
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()

    print("  [Step 4] Converting HTML to Markdown...")

    # Configure html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.body_width = 0
    h.unicode_snob = True
    h.skip_internal_links = True

    # Convert to markdown
    markdown_content = h.handle(str(soup))

    # Clean up excessive blank lines
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

    print("  [Step 5] Combining SEC header + Markdown content...")

    # Combine: SEC header + separator + markdown
    final_content = ""

    if sec_header:
        final_content += sec_header + "\n\n"
        final_content += "=" * 80 + "\n\n"

    final_content += markdown_content

    print("  [Step 6] Writing output...")

    # Write output
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"  [OK] Converted successfully")
    print(f"  [Output] {output_md_path}")
    print(f"  [Size] {len(final_content):,} characters")
    if sec_header:
        print(f"  [Note] SEC-HEADER preserved at top of file")

    return True

def main():
    input_file = Path("C:/Users/kabec/Downloads/20240202_10-Q_edgar_data_320193_0000320193-24-000006_texttomarkdown.txt")
    output_file = Path("C:/Users/kabec/Downloads/20240202_10-Q_edgar_data_320193_0000320193-24-000006.md")

    print("="*80)
    print("SEC .TXT TO MARKDOWN CONVERTER (Single File)")
    print("Preserves SEC-HEADER metadata")
    print("="*80)

    if not input_file.exists():
        print(f"\n[ERROR] File not found: {input_file}")
        return

    print(f"\nInput: {input_file.name}")
    print(f"Output: {output_file.name}")

    try:
        if convert_txt_to_markdown(input_file, output_file):
            print("\n" + "="*80)
            print("SUCCESS!")
            print("="*80)
        else:
            print("\n[ERROR] Conversion failed")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
