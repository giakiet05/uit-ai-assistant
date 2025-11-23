"""
Test Gemini Markdown Fixer with file 547.

This test:
1. Reads the deformed markdown from processed/regulation/547...md
2. Fixes it using GeminiMarkdownFixer
3. Saves output to test/test_fixer_output.md
"""

from pathlib import Path
from src.processing.llm_markdown_fixer import GeminiMarkdownFixer

# Hardcoded path to file 547
INPUT_FILE = Path("data/processed/regulation/547-qd-dhcntt_30-8-2019_qui_dinh_dao_tao_ngoai_ngu_doi_voi_he_chinh_qui_khoa_2019_0_0.md")
OUTPUT_FILE = Path("test/test_fixer_output.md")


def test_fixer():
    """Test Gemini fixer with file 547."""

    print("=" * 60)
    print("Testing Gemini Markdown Fixer")
    print("=" * 60)

    # Check input file exists
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    print(f"📄 Input file: {INPUT_FILE}")
    print(f"📝 Output file: {OUTPUT_FILE}")

    # Read input
    print("\n[1/3] Reading input markdown...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        original_md = f.read()

    print(f"  ✅ Read {len(original_md)} characters")
    print(f"  ✅ Lines: {len(original_md.splitlines())}")

    # Initialize fixer
    print("\n[2/3] Initializing Gemini fixer...")
    try:
        fixer = GeminiMarkdownFixer()
        print(f"  ✅ Model: {fixer.model_name}")
        print(f"  ✅ Temperature: {fixer.temperature}")
        print(f"  ✅ Max output tokens: {fixer.max_output_tokens}")
        print(f"  ✅ Rate limit: {fixer.rpm} RPM")
    except Exception as e:
        print(f"  ❌ Error initializing fixer: {e}")
        return

    # Fix markdown
    print("\n[3/3] Fixing markdown with Gemini...")
    try:
        fixed_md = fixer.fix_markdown(original_md)
        print(f"  ✅ Fixed! Output: {len(fixed_md)} characters")
        print(f"  ✅ Lines: {len(fixed_md.splitlines())}")
    except Exception as e:
        print(f"  ❌ Error fixing markdown: {e}")
        return

    # Save output
    print(f"\n[SAVE] Saving to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(fixed_md)

    print(f"  ✅ Saved!")

    # Show preview
    print("\n" + "=" * 60)
    print("PREVIEW (first 1000 chars):")
    print("=" * 60)
    print(fixed_md[:1000])
    print("=" * 60)

    print(f"\n✅ Done! Check output at: {OUTPUT_FILE}")


if __name__ == "__main__":
    test_fixer()
