"""
Processing Pipeline - Stage 1: Parse & Clean

This pipeline:
1. For .md files → Clean using category-specific cleaner (letterhead removal + navigation cleanup)
2. For .pdf/.docx → Parse to markdown, then clean with cleaner (letterhead removal + navigation cleanup)
3. Apply content filter to check quality
4. Save good content to processed/, reject bad content to .rejected/

NOTE: This stage does NOT generate metadata. Run pipeline_metadata.py separately.
"""

import json
from pathlib import Path
from typing import List, Optional

from src.config.settings import settings
from src.processing.parser.parser_factory import ParserFactory
from src.processing.cleaner.cleaner_factory import CleanerFactory
from src.processing.content_filter import ContentFilter


class ParseCleanPipeline:
    """
    Stage 1: Parse/Clean raw files and save processed markdown.
    Does NOT generate metadata (that's Stage 2).
    """

    def __init__(self):
        """Initialize the parse/clean pipeline."""
        self.content_filter = ContentFilter()

        # Stats tracking
        self.stats = {
            "files_processed": 0,
            "files_skipped_existing": 0,
            "files_skipped_unsupported": 0,
            "files_rejected": 0,
            "files_failed": 0,
            "errors": []
        }

    def run(self, categories: Optional[List[str]] = None, force: bool = False):
        """
        Run the parse/clean pipeline.

        Args:
            categories: List of specific categories to process (e.g., ["regulation"]).
                        If None, all categories in the raw data directory will be processed.
            force: If True, re-process existing files (overwrite)
        """
        print("\n" + "="*70)
        print(f"🚀 STAGE 1: PARSE & CLEAN PIPELINE - START")
        print("="*70 + "\n")

        raw_data_path = settings.paths.RAW_DATA_DIR
        if not raw_data_path.exists():
            print(f"[ERROR] Raw data directory not found: {raw_data_path}")
            return

        # Determine which category directories to process
        if categories:
            category_dirs = [raw_data_path / cat for cat in categories if (raw_data_path / cat).is_dir()]
        else:
            category_dirs = [d for d in raw_data_path.iterdir() if d.is_dir()]

        print(f"📊 FOUND {len(category_dirs)} CATEGORIES: {[d.name for d in category_dirs]}\n")

        # Process each category
        for category_dir in category_dirs:
            category = category_dir.name
            print(f"\n{'='*70}")
            print(f"📁 PROCESSING CATEGORY: {category.upper()}")
            print(f"{'='*70}\n")

            files_to_process = [f for f in category_dir.iterdir() if f.is_file()]
            total = len(files_to_process)

            for idx, file_path in enumerate(files_to_process, 1):
                print(f"[{idx}/{total}] ", end="")
                self.process_file(file_path, category, force=force)

        self._print_stats()

    def process_file(self, file_path: Path, category: str, force: bool = False):
        """
        Process a single file: parse/clean and save if quality is good.

        Args:
            file_path: Path to raw file
            category: Document category (regulation, curriculum, etc.)
            force: If True, overwrite existing processed file
        """
        filename = file_path.name

        # Skip unsupported file types early
        if file_path.suffix.lower() in ['.xlsx', '.json']:
            print(f"[SKIP] Unsupported file type: {filename}")
            self.stats["files_skipped_unsupported"] += 1
            return

        # Check if already processed
        processed_dir = settings.paths.PROCESSED_DATA_DIR / category
        processed_md = processed_dir / f"{file_path.stem}.md"

        if processed_md.exists() and not force:
            print(f"[SKIP] Already processed: {filename}")
            self.stats["files_skipped_existing"] += 1
            return

        print(f"Processing: {filename}")

        try:
            # Step 1: Parse or Clean based on file type
            cleaner = CleanerFactory.get_cleaner(category)

            if file_path.suffix.lower() == '.md':
                # MD file → Clean only
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()

                processed_content = cleaner.clean(raw_content)
                print(f"  → Cleaned .md file")
            else:
                # PDF/DOCX → Parse then clean
                parser = ParserFactory.get_parser(str(file_path))
                parsed_content = parser.parse(str(file_path))

                # Apply cleaner to parsed content (including letterhead removal)
                processed_content = cleaner.clean(parsed_content)
                print(f"  → Parsed {file_path.suffix} file and cleaned")

            # Validate content exists
            if not processed_content or not processed_content.strip():
                print(f"  ⚠️  [WARNING] No content extracted")
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "file": filename,
                    "category": category,
                    "error": "No content extracted"
                })
                return

            # Step 2: Apply content filter
            is_useful, reason = self.content_filter.is_useful(processed_content)

            if not is_useful:
                print(f"  ❌ [REJECTED] Content quality too low: {reason}")
                self._save_rejected_file(
                    content=processed_content,
                    file_path=file_path,
                    category=category,
                    reason=reason
                )
                self.stats["files_rejected"] += 1
                return

            # Step 3: Save processed markdown
            processed_dir.mkdir(parents=True, exist_ok=True)
            with open(processed_md, 'w', encoding='utf-8') as f:
                f.write(processed_content)

            self.stats["files_processed"] += 1
            print(f"  ✅ [SUCCESS] Saved: {processed_md.name}")

        except Exception as e:
            print(f"  ❌ [ERROR] Failed: {str(e)[:80]}")
            self.stats["files_failed"] += 1
            self.stats["errors"].append({
                "file": filename,
                "category": category,
                "error": str(e)
            })

    def _save_rejected_file(self, content: str, file_path: Path, category: str, reason: str):
        """
        Save rejected content to .rejected/ folder with metadata about why it was rejected.

        Args:
            content: Processed content that was rejected
            file_path: Original file path
            category: Document category
            reason: Rejection reason
        """
        rejected_dir = settings.paths.PROCESSED_DATA_DIR / ".rejected" / category
        rejected_dir.mkdir(parents=True, exist_ok=True)

        # Save rejected markdown
        rejected_md = rejected_dir / f"{file_path.stem}.md"
        with open(rejected_md, 'w', encoding='utf-8') as f:
            f.write(content)

        # Save rejection metadata
        rejection_info = {
            "original_file": str(file_path),
            "category": category,
            "rejection_reason": reason,
            "stats": self.content_filter.get_stats_summary(content)
        }

        rejected_json = rejected_dir / f"{file_path.stem}.json"
        with open(rejected_json, 'w', encoding='utf-8') as f:
            json.dump(rejection_info, f, ensure_ascii=False, indent=2)

    def _print_stats(self):
        """Print final processing statistics."""
        print("\n" + "="*70)
        print("📊 STAGE 1 COMPLETE - STATISTICS")
        print("="*70)
        print(f"   Files processed:       {self.stats['files_processed']}")
        print(f"   Files skipped (exist):  {self.stats['files_skipped_existing']}")
        print(f"   Files skipped (type):   {self.stats['files_skipped_unsupported']}")
        print(f"   Files rejected (low quality): {self.stats['files_rejected']}")
        print(f"   Files failed:          {self.stats['files_failed']}")

        if self.stats["errors"]:
            print(f"\n   ⚠️  {len(self.stats['errors'])} ERRORS:")
            for err in self.stats["errors"][:10]:
                print(f"      • {err['file']}: {str(err['error'])[:60]}")
            if len(self.stats["errors"]) > 10:
                print(f"      ... and {len(self.stats['errors']) - 10} more")

        print("\n💡 Next step: Run pipeline_metadata.py to generate metadata")
        print("="*70 + "\n")


def run_parse_clean(categories: Optional[List[str]] = None, force: bool = False):
    """
    Convenience function to run the parse/clean pipeline.

    Args:
        categories: List of categories to process
        force: If True, re-process existing files
    """
    pipeline = ParseCleanPipeline()
    pipeline.run(categories=categories, force=force)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Stage 1: Parse & Clean Pipeline')
    parser.add_argument(
        '--categories', '-c',
        type=str,
        help='Comma-separated categories to process (e.g., regulation,curriculum)'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force re-process existing files'
    )

    args = parser.parse_args()

    cats = args.categories.split(',') if args.categories else None
    run_parse_clean(categories=cats, force=args.force)
