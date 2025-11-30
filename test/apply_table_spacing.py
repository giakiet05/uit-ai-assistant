"""
Apply rule-based table spacing post-processing to already-fixed curriculum files.

This script applies ONLY the _ensure_table_blank_lines() function to files
in data/fixed/curriculum/ WITHOUT calling the LLM again (saves time and money).

Usage:
    python test/apply_table_spacing.py
"""

from pathlib import Path
from src.knowledge_builder.processing.llm_markdown_fixer import MarkdownFixer


def apply_table_spacing():
    """
    Apply table spacing post-processing to all files in data/fixed/curriculum/.

    This reads each file, applies _ensure_table_blank_lines(), and overwrites the file.
    """
    # Paths
    fixed_dir = Path("data/fixed/curriculum")

    if not fixed_dir.exists():
        print(f"❌ Directory not found: {fixed_dir}")
        return

    # Get all .md files
    md_files = sorted(fixed_dir.glob("*.md"))

    if not md_files:
        print(f"❌ No .md files found in {fixed_dir}")
        return

    print(f"[APPLY TABLE SPACING]")
    print(f"Directory: {fixed_dir}")
    print(f"Found:     {len(md_files)} files\n")
    print("="*60)

    # Create fixer instance (we only use the _ensure_table_blank_lines method)
    # No LLM calls, so this is fast!
    fixer = MarkdownFixer()

    success_count = 0
    error_count = 0

    for idx, file_path in enumerate(md_files, 1):
        print(f"\n[{idx}/{len(md_files)}] {file_path.name}")

        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()

            print(f"  📄 Original: {len(original)} chars")

            # Apply rule-based post-processing (NO LLM!)
            fixed = fixer._ensure_table_blank_lines(original)

            print(f"  ✅ Fixed:    {len(fixed)} chars ({len(fixed) - len(original):+d})")

            # Overwrite file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed)

            print(f"  💾 Saved:    {file_path.name}")
            success_count += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1
            continue

    # Summary
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"  ✅ Success: {success_count}/{len(md_files)}")
    print(f"  ❌ Error:   {error_count}/{len(md_files)}")
    print(f"\nDirectory: {fixed_dir.absolute()}")


if __name__ == "__main__":
    apply_table_spacing()
