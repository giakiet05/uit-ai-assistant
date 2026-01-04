"""
Processing Pipeline - Stage 2: Metadata Generation

This pipeline:
1. Reads processed markdown files from processed/ directory
2. Generates metadata_generator using LLM (category-specific generators)
3. Saves metadata_generator as JSON alongside markdown

NOTE: Run pipeline_parse_clean.py first to generate processed markdown files.
This stage only reads existing .md files and generates metadata_generator.
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ...config import settings
from ..metadata_generator.metadata_generator_factory import MetadataGeneratorFactory


class MetadataPipeline:
    """
    Stage 2: Generate metadata_generator for processed markdown files.
    Does NOT parse/clean (reads from already processed files).
    """

    def __init__(self):
        """Initialize the metadata_generator generation pipeline."""
        # Stats tracking
        self.stats = {
            "files_processed": 0,
            "files_skipped_existing": 0,
            "files_skipped_no_md": 0,
            "files_failed": 0,
            "errors": []
        }

    def run(self, categories: Optional[List[str]] = None, force: bool = False):
        """
        Run the metadata_generator generation pipeline.

        Args:
            categories: List of specific categories to process (e.g., ["regulation"]).
                        If None, all categories in the processed directory will be processed.
            force: If True, regenerate metadata_generator even if .json exists
        """
        print("\n" + "="*70)
        print(f" STAGE 2: METADATA GENERATION PIPELINE - START")
        print("="*70 + "\n")

        processed_data_path = settings.paths.PROCESSED_DATA_DIR
        if not processed_data_path.exists():
            print(f"[ERROR] Processed data directory not found: {processed_data_path}")
            print(f"[INFO] Run pipeline_parse_clean.py first to generate processed files")
            return

        # Determine which category directories to process
        if categories:
            category_dirs = [processed_data_path / cat for cat in categories
                           if (processed_data_path / cat).is_dir()]
        else:
            # Exclude .rejected folder
            category_dirs = [d for d in processed_data_path.iterdir()
                           if d.is_dir() and not d.name.startswith('.')]

        print(f" FOUND {len(category_dirs)} CATEGORIES: {[d.name for d in category_dirs]}\n")

        # Process each category
        for category_dir in category_dirs:
            category = category_dir.name
            print(f"\n{'='*70}")
            print(f" PROCESSING CATEGORY: {category.upper()}")
            print(f"{'='*70}\n")

            # Get all .md files
            md_files = list(category_dir.glob("*.md"))
            total = len(md_files)

            if total == 0:
                print(f"[INFO] No markdown files found in {category}/")
                continue

            for idx, md_path in enumerate(md_files, 1):
                print(f"[{idx}/{total}] ", end="")
                self.process_file(md_path, category, force=force)

        self._print_stats()

    def process_file(self, md_path: Path, category: str, force: bool = False):
        """
        Generate metadata_generator for a processed markdown file.

        Args:
            md_path: Path to processed .md file
            category: Document category (regulation, curriculum, etc.)
            force: If True, regenerate metadata_generator even if .json exists
        """
        filename = md_path.name
        json_path = md_path.with_suffix('.json')

        # Check if metadata_generator already exists
        if json_path.exists() and not force:
            print(f"[SKIP] Metadata exists: {filename}")
            self.stats["files_skipped_existing"] += 1
            return

        print(f"Processing: {filename}")

        try:
            # Step 1: Read processed markdown (NO parsing!)
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content or not content.strip():
                print(f"    [WARNING] Empty markdown file")
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "file": filename,
                    "category": category,
                    "error": "Empty markdown file"
                })
                return

            # Step 2: Generate metadata_generator using category-specific generator
            generator = MetadataGeneratorFactory.get_generator(category)
            metadata_obj = generator.generate(md_path, content)

            if not metadata_obj:
                print(f"   [ERROR] Metadata generation failed")
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "file": filename,
                    "category": category,
                    "error": "Metadata generator returned None"
                })
                return

            # Step 3: Validate metadata_generator (basic checks)
            if not metadata_obj.title or not metadata_obj.category:
                print(f"    [WARNING] Invalid metadata_generator: missing title/category")
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "file": filename,
                    "category": category,
                    "error": "Invalid metadata_generator: missing critical fields"
                })
                return

            # Step 4: Save metadata_generator JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                # Use Pydantic's model_dump for serialization
                metadata_dict = metadata_obj.model_dump()

                # Add generation timestamp
                metadata_dict["_generated_at"] = datetime.now().isoformat()

                json.dump(metadata_dict, f, ensure_ascii=False, indent=2)

            self.stats["files_processed"] += 1
            print(f"   [SUCCESS] Saved metadata_generator: {json_path.name}")
            print(f"     -> Title: {metadata_obj.title[:60]}...")
            print(f"     -> Type: {getattr(metadata_obj, 'document_type', 'N/A')}")

        except Exception as e:
            print(f"   [ERROR] Failed: {str(e)[:80]}")
            self.stats["files_failed"] += 1
            self.stats["errors"].append({
                "file": filename,
                "category": category,
                "error": str(e)
            })

            # Print traceback for debugging
            import traceback
            traceback.print_exc()

    def _print_stats(self):
        """Print final processing statistics."""
        print("\n" + "="*70)
        print(" STAGE 2 COMPLETE - STATISTICS")
        print("="*70)
        print(f"   Metadata generated:     {self.stats['files_processed']}")
        print(f"   Files skipped (exist):  {self.stats['files_skipped_existing']}")
        print(f"   Files skipped (no md):  {self.stats['files_skipped_no_md']}")
        print(f"   Files failed:           {self.stats['files_failed']}")

        if self.stats["errors"]:
            print(f"\n     {len(self.stats['errors'])} ERRORS:")
            for err in self.stats["errors"][:10]:
                print(f"      • {err['file']}: {str(err['error'])[:60]}")
            if len(self.stats["errors"]) > 10:
                print(f"      ... and {len(self.stats['errors']) - 10} more")

        print("\n Files are ready for indexing!")
        print("="*70 + "\n")


def run_metadata_generation(categories: Optional[List[str]] = None, force: bool = False):
    """
    Convenience function to run the metadata_generator generation pipeline.

    Args:
        categories: List of categories to process
        force: If True, regenerate metadata_generator even if exists
    """
    pipeline = MetadataPipeline()
    pipeline.run(categories=categories, force=force)
