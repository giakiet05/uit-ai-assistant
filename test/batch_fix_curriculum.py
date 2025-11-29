"""
Batch fix tất cả curriculum markdown files.

Usage:
    python test/batch_fix_curriculum.py
"""

from pathlib import Path
from src.processing.llm_markdown_fixer import MarkdownFixer


def batch_fix_curriculum():
    """Fix tất cả curriculum files và lưu vào data/fixed/curriculum."""
    
    # Paths
    input_dir = Path("data/processed/curriculum")
    output_dir = Path("data/fixed/curriculum")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all .md files
    all_md_files = sorted(input_dir.glob("*.md"))

    if not all_md_files:
        print(f"❌ No .md files found in {input_dir}")
        return

    # Filter out files that already exist in output directory
    md_files = []
    skipped_files = []

    for md_file in all_md_files:
        output_file = output_dir / md_file.name
        if output_file.exists():
            skipped_files.append(md_file)
        else:
            md_files.append(md_file)

    print(f"[BATCH FIX CURRICULUM]")
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Found:  {len(all_md_files)} files")
    print(f"Skipped: {len(skipped_files)} files (already fixed)")
    print(f"To process: {len(md_files)} files\n")

    if not md_files:
        print("✅ All files already fixed!")
        return
    
    # Create fixer
    print("Creating MarkdownFixer...")
    fixer = MarkdownFixer()
    
    # Estimate time
    print(f"Estimated time: {len(md_files) * fixer.min_delay / 60:.1f} minutes\n")
    print("="*60)
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for idx, input_file in enumerate(md_files, 1):
        print(f"\n[{idx}/{len(md_files)}] {input_file.name}")
        
        try:
            # Read input
            with open(input_file, encoding='utf-8') as f:
                original = f.read()
            
            print(f"  📄 Original: {len(original)} chars")
            
            # Fix with curriculum prompt
            fixed = fixer.fix_markdown(original, category="curriculum")
            
            print(f"  ✅ Fixed:    {len(fixed)} chars ({len(fixed) - len(original):+d})")
            
            # Save to output directory with same filename
            output_file = output_dir / input_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(fixed)
            
            print(f"  💾 Saved:    {output_file.name}")
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
    print(f"\nOutput directory: {output_dir.absolute()}")


if __name__ == "__main__":
    batch_fix_curriculum()
