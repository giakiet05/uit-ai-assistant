"""
Test MarkdownFixer với cả regulation và curriculum.

Usage:
    # Test curriculum
    python test/test_markdown_fixer_refactored.py curriculum

    # Test regulation
    python test/test_markdown_fixer_refactored.py regulation
"""

import sys
from pathlib import Path
from src.processing.llm_markdown_fixer import MarkdownFixer


def test_curriculum():
    """Test curriculum markdown fixer."""

    # Paths
    input_file = Path("data/processed/curriculum/content-chuong-trinh-dao-tao-song-nganh-nganh-thuong-mai-dien-tu-ap-dung-tu-khoa-19-2024.md")
    output_file = Path("test/test_curriculum_fixed_refactored.md")

    print(f"[CURRICULUM TEST]")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}\n")

    # Read input
    with open(input_file, encoding='utf-8') as f:
        original_markdown = f.read()

    print(f"Original length: {len(original_markdown)} chars\n")

    # Create fixer
    print("Creating MarkdownFixer...")
    fixer = MarkdownFixer()

    # Fix with curriculum category
    print("Fixing curriculum markdown...")
    fixed_markdown = fixer.fix_markdown(original_markdown, category="curriculum")

    print(f"✅ Fixed: {len(fixed_markdown)} chars\n")

    # Save output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_markdown)

    print(f"✅ Saved to: {output_file}")

    # Stats
    print("\n" + "="*50)
    print("STATISTICS:")
    print(f"Original: {len(original_markdown)} chars")
    print(f"Fixed:    {len(fixed_markdown)} chars")
    print(f"Diff:     {len(fixed_markdown) - len(original_markdown):+d} chars")


def test_regulation():
    """Test regulation markdown fixer (existing functionality)."""

    print("[REGULATION TEST]")
    print("Regulation test not implemented in this script.")
    print("Use existing test files for regulation testing.")


if __name__ == "__main__":
    category = sys.argv[1] if len(sys.argv) > 1 else "curriculum"

    if category == "curriculum":
        test_curriculum()
    elif category == "regulation":
        test_regulation()
    else:
        print(f"❌ Invalid category: {category}")
        print("Usage: python test/test_markdown_fixer_refactored.py [curriculum|regulation]")
        sys.exit(1)
