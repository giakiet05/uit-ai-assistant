"""
CLI command to fix markdown structure using Gemini LLM.

Usage:
    ua fix-markdown --category regulation
    ua fix-markdown --category curriculum
    ua fix-markdown --file data/processed/regulation/abc.md
    ua fix-markdown --category regulation --dry-run
"""

from pathlib import Path
from typing import Optional

from ..processing.llm_markdown_fixer import MarkdownFixer
from ..config import settings


def fix_markdown_command(
    category: Optional[str] = None,
    file_path: Optional[str] = None,
    dry_run: bool = False
):
    """
    Fix markdown structure using Gemini LLM.

    Args:
        category: Category to fix (regulation, curriculum, etc.)
        file_path: Single file to fix (if specified, category is ignored)
        dry_run: If True, only show preview without saving changes
    """
    # Validate inputs
    if not category and not file_path:
        print("❌ Error: Must specify --category or --file")
        print("\nExamples:")
        print("  ua fix-markdown --category regulation")
        print("  ua fix-markdown --file data/processed/regulation/abc.md")
        return

    # Initialize fixer
    try:
        fixer = MarkdownFixer()
    except ValueError as e:
        print(f"❌ {e}")
        print("\nPlease set GOOGLE_API_KEY in .env file:")
        print("  1. Go to https://aistudio.google.com/apikey")
        print("  2. Create API key")
        print("  3. Add to .env: GOOGLE_API_KEY=your_key_here")
        return

    # Determine input files
    if file_path:
        # Single file mode
        input_path = Path(file_path)
        if not input_path.exists():
            print(f"❌ File not found: {file_path}")
            return

        print(f"[FIX] Single file mode: {input_path.name}")
        files_to_fix = [input_path]
        output_dir = input_path.parent

    elif category:
        # Batch mode for category
        input_dir = settings.paths.PROCESSED_DATA_DIR / category
        if not input_dir.exists():
            print(f"❌ Category directory not found: {input_dir}")
            print(f"\nAvailable categories:")
            for cat_dir in settings.paths.PROCESSED_DATA_DIR.iterdir():
                if cat_dir.is_dir():
                    print(f"  - {cat_dir.name}")
            return

        files_to_fix = list(input_dir.glob("*.md"))
        output_dir = input_dir

        if not files_to_fix:
            print(f"❌ No markdown files found in {input_dir}")
            return

        print(f"[FIX] Batch mode: {category}")
        print(f"[FIX] Found {len(files_to_fix)} markdown files")
        print(f"[FIX] Estimated time: {len(files_to_fix) * fixer.min_delay / 60:.1f} minutes")

    # Dry run info
    if dry_run:
        print("\n" + "=" * 60)
        print("🔍 DRY RUN MODE - No files will be modified")
        print("=" * 60 + "\n")

    # Process files
    success_count = 0
    error_count = 0

    for idx, md_file in enumerate(files_to_fix, 1):
        print(f"\n[{idx}/{len(files_to_fix)}] Processing: {md_file.name}")

        try:
            # Read original
            with open(md_file, encoding='utf-8') as f:
                original = f.read()

            # Fix with Gemini
            fixed = fixer.fix_markdown(original)

            if dry_run:
                # Show preview
                print("\n  📋 PREVIEW (first 800 characters):")
                print("  " + "─" * 58)
                preview = fixed[:800].replace("\n", "\n  ")
                print("  " + preview)
                if len(fixed) > 800:
                    print("  " + "─" * 58)
                    print(f"  ... ({len(fixed) - 800} more characters)")
                print("  " + "─" * 58)

            else:
                # Save (in-place)
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(fixed)
                print(f"  ✅ Fixed and saved")

            success_count += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1
            continue

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Success: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(files_to_fix)}")
    if dry_run:
        print("ℹ️  Dry run - no files were modified")
    else:
        print(f"💾 Files saved to: {output_dir}")
    print("=" * 60)
