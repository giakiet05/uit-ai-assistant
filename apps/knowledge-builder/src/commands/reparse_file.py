"""
Re-parse a single PDF file to restore original markdown (before Gemini fixer).

Usage:
    python -m src.commands.reparse_file <pdf_filename>

Example:
    python -m src.commands.reparse_file 547
"""

import sys
from ..config.settings import settings


def reparse_file(file_identifier: str):
    """
    Re-parse a single PDF file by name/ID.

    Args:
        file_identifier: Filename (with or without .pdf), or partial match
                        Example: "547", "547.pdf", "547-qd-dhcntt"
    """
    # ========== FIND PDF FILE ==========

    raw_dir = settings.paths.RAW_DATA_DIR / "regulation"

    # Find matching PDF
    matches = list(raw_dir.glob(f"*{file_identifier}*.pdf"))

    if not matches:
        print(f"❌ No PDF found matching: {file_identifier}")
        print(f"   Searched in: {raw_dir}")
        return

    if len(matches) > 1:
        print(f"❌ Multiple PDFs found matching '{file_identifier}':")
        for m in matches:
            print(f"   - {m.name}")
        print("\n   Please be more specific!")
        return

    pdf_file = matches[0]
    print(f"✅ Found PDF: {pdf_file.name}\n")

    # ========== PARSE WITH LLAMAPARSE ==========

    print("[1/2] Parsing PDF with LlamaParse...")
    print("      (This will take ~30-60 seconds)\n")

    try:
        from llama_parse import LlamaParse

        parser = LlamaParse(
            api_key=settings.credentials.LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            verbose=True
        )

        documents = parser.load_data(str(pdf_file))

        if not documents:
            print("❌ LlamaParse returned empty result!")
            return

        markdown_content = documents[0].text
        print(f"✅ Parsed successfully ({len(markdown_content)} chars)\n")

    except Exception as e:
        print(f"❌ Parse error: {e}")
        return

    # ========== SAVE TO PROCESSED DIR ==========

    print("[2/2] Saving original markdown (no Gemini fix)...")

    processed_dir = settings.paths.PROCESSED_DATA_DIR / "regulation"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Output filename: same as PDF but .md extension
    output_file = processed_dir / pdf_file.name.replace('.pdf', '.md')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✅ Saved to: {output_file}")
    print(f"\n📝 File has been restored to ORIGINAL markdown (before Gemini fix)")
    print(f"   If you want to fix it again, run:")
    print(f"   python -m src.commands.fix_markdown {output_file.stem}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.commands.reparse_file <pdf_filename>")
        print("\nExample:")
        print("  python -m src.commands.reparse_file 547")
        print("  python -m src.commands.reparse_file 547-qd-dhcntt")
        sys.exit(1)

    file_id = sys.argv[1]
    reparse_file(file_id)
