"""
Convert SEC HTML filings to clean Markdown format
Handles XBRL HTML files from SEC EDGAR
"""
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import html2text

sys.stdout.reconfigure(encoding='utf-8')

def convert_html_to_markdown(html_file_path, output_md_path):
    """
    Convert SEC HTML filing to Markdown format

    Args:
        html_file_path: Path to HTML file
        output_md_path: Path for output Markdown file
    """
    print(f"\n[Processing] {Path(html_file_path).name}")

    # Read HTML file
    with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove hidden XBRL metadata sections
    for hidden in soup.find_all(['ix:hidden', 'ix:header'], recursive=True):
        hidden.decompose()

    # Remove script and style tags
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()

    # Configure html2text converter
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    h.unicode_snob = True
    h.skip_internal_links = True

    # Convert to markdown
    markdown_content = h.handle(str(soup))

    # Clean up the markdown
    # Remove excessive blank lines (more than 2 in a row)
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

    # Clean up table formatting
    # html2text creates pipe tables, which is what we want

    # Write output
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  [OK] Converted to Markdown")
    print(f"  [Output] {output_md_path}")
    print(f"  [Size] {len(markdown_content):,} characters")

    return True

def main():
    """Convert all HTML files in downloads folder to Markdown"""

    input_dir = Path("C:/Users/kabec/Downloads/2024q4_filings")
    output_dir = Path("C:/Users/kabec/Downloads/2024q4_filings/markdown")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("="*80)
    print("SEC HTML TO MARKDOWN CONVERTER")
    print("="*80)
    print(f"\nInput directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Find all HTML files
    html_files = list(input_dir.glob("*.html"))

    if not html_files:
        print("[ERROR] No HTML files found in input directory")
        return

    print(f"Found {len(html_files)} HTML files:")
    for file in html_files:
        print(f"  - {file.name}")
    print()

    # Convert each file
    success_count = 0
    for html_file in html_files:
        # Generate output filename
        output_filename = html_file.stem + ".md"
        output_path = output_dir / output_filename

        try:
            if convert_html_to_markdown(html_file, output_path):
                success_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to convert {html_file.name}: {e}")

    print("\n" + "="*80)
    print(f"COMPLETED: {success_count}/{len(html_files)} files converted successfully")
    print("="*80)

    if success_count == len(html_files):
        print(f"\n[OK] All files converted to Markdown")
        print(f"\nOutput files in: {output_dir}")
        for md_file in output_dir.glob("*.md"):
            size_kb = md_file.stat().st_size / 1024
            print(f"  - {md_file.name} ({size_kb:.1f} KB)")

if __name__ == '__main__':
    # Check if required libraries are available
    try:
        import bs4
        import html2text
    except ImportError as e:
        print("[ERROR] Required library not found:")
        print(f"  {e}")
        print("\nPlease install required libraries:")
        print("  pip install beautifulsoup4 html2text")
        sys.exit(1)

    main()
