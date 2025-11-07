"""
Processing Pipeline V2 - Category-based document processing with metadata.

This pipeline:
1. Categorizes folders (regulation, curriculum, announcement, other)
2. Filters by target categories (Phase 1: regulation + curriculum only)
3. Processes each folder:
   - Parses files to markdown using LlamaParser
   - Generatvel metadata
   - Saves to flat structure: processed/{domain}/{category}/
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional

from src.config.settings import settings
from src.processing.categorizer import FolderCategorizer
from src.processing.metadata_generator import DocumentMetadataGenerator
from src.processing.content_filter import ContentFilter
from src.processing.parser.parser_factory import ParserFactory
from src.processing.cleaner.cleaner_factory import CleanerFactory


class ProcessingPipelineV2:
    """
    Main processing pipeline for transforming raw crawled data into
    categorized, metadata-enriched markdown documents.
    """

    def __init__(self, domain: str = "daa.uit.edu.vn"):
        """
        Initialize pipeline for a specific domain.

        Args:
            domain: Domain name (e.g., "daa.uit.edu.vn")
        """
        self.domain = domain
        self.categorizer = FolderCategorizer()
        self.metadata_generator = DocumentMetadataGenerator()
        self.content_filter = ContentFilter()
        self.cleaner = CleanerFactory.get_cleaner(domain)

        # Stats tracking
        self.stats = {
            "folders_processed": 0,
            "folders_skipped": 0,
            "files_processed": 0,
            "files_skipped": 0,  # Already processed, resume support
            "files_filtered": 0,
            "files_failed": 0,
            "filter_reasons": {},
            "errors": []
        }

    def run(self, categories: Optional[List[str]] = None):
        """
        Run the processing pipeline.

        Args:
            categories: List of categories to process (None = use settings)
        """
        if categories is None:
            categories = settings.processing.PROCESS_CATEGORIES

        print("\n" + "="*70)
        print(f"🚀 PROCESSING PIPELINE V2 - START")
        print(f"   Domain: {self.domain}")
        print(f"   Categories: {', '.join(categories)}")
        print("="*70 + "\n")

        # Get raw domain path
        raw_domain_path = settings.paths.RAW_DATA_DIR / self.domain

        if not raw_domain_path.exists():
            print(f"[ERROR] Raw domain directory not found: {raw_domain_path}")
            return

        # Get folders by category
        folders_by_category = self.categorizer.get_folders_by_category(
            raw_domain_path,
            categories=categories
        )

        # Print summary
        total_folders = sum(len(folders) for folders in folders_by_category.values())
        print(f"📊 FOUND {total_folders} FOLDERS TO PROCESS:\n")
        for cat, folders in folders_by_category.items():
            print(f"   {cat.upper():15} {len(folders):3} folders")
        print()

        # Process each category
        for category, folders in folders_by_category.items():
            if not folders:
                continue

            print(f"\n{'='*70}")
            print(f"📁 PROCESSING CATEGORY: {category.upper()}")
            print(f"{'='*70}\n")

            for folder_path in folders:
                self.process_folder(folder_path, category)

        # Print final stats
        self._print_stats()

    def process_folder(self, folder_path: Path, category: str):
        """
        Process a single folder: parse files and generate metadata.

        Args:
            folder_path: Path to raw folder
            category: Folder category (regulation, curriculum, etc.)
        """
        folder_name = folder_path.name
        print(f"\n--- Processing folder: {folder_name} [{category}] ---")

        # Load page metadata (from raw/domain/folder/metadata.json)
        metadata_path = folder_path / "metadata.json"
        page_metadata = self._load_page_metadata(metadata_path)

        if not page_metadata:
            print(f"[WARNING] No page metadata found, using defaults")
            page_metadata = {}

        # Get files to process (skip metadata.json)
        files_to_process = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.name != "metadata.json"
        ]

        if not files_to_process:
            print(f"[INFO] No files to process in folder")
            self.stats["folders_skipped"] += 1
            return

        # Process each file
        processed_count = 0
        for file_path in files_to_process:
            try:
                success = self.process_file(
                    file_path=file_path,
                    folder_name=folder_name,
                    page_metadata=page_metadata,
                    category=category
                )
                if success:
                    processed_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to process {file_path.name}: {e}")
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "folder": folder_name,
                    "file": file_path.name,
                    "error": str(e)
                })

        self.stats["folders_processed"] += 1
        print(f"--- Finished folder: {processed_count}/{len(files_to_process)} files processed ---")

    def process_file(
        self,
        file_path: Path,
        folder_name: str,
        page_metadata: Dict,
        category: str
    ) -> bool:
        """
        Process a single file: clean/parse to markdown, filter, and generate metadata.

        Args:
            file_path: Path to file
            folder_name: Parent folder name (for document_id)
            page_metadata: Page-level metadata dict
            category: Folder category

        Returns:
            True if successful, False otherwise
        """
        filename = file_path.name
        filename_stem = file_path.stem

        # Skip XLSX files (structured data - use SQL database instead)
        if file_path.suffix.lower() == '.xlsx':
            print(f"[SKIP] XLSX file (use SQL database): {filename}")
            self.stats["files_skipped"] += 1
            return True

        # Check if already processed (resume support)
        # Use same document_id generation logic as metadata_generator
        document_id = f"{folder_name}__{filename_stem}"
        document_id = re.sub(r'[^\w\-]', '-', document_id)  # Sanitize

        category_dir = settings.paths.PROCESSED_DATA_DIR / self.domain / category
        existing_md = category_dir / f"{document_id}.md"

        if existing_md.exists():
            print(f"[SKIP] Already processed: {filename}")
            self.stats["files_skipped"] += 1
            return True

        print(f"[INFO] Processing: {filename}")

        try:
            # Handle content.md differently (clean + filter)
            if filename == "content.md":
                markdown_content = self._clean_and_filter_content(file_path, folder_name)
                if not markdown_content:
                    return False  # Filtered out
            else:
                # Parse attachments (PDF, DOCX, etc.)
                parser = ParserFactory.get_parser(
                    str(file_path),
                    use_llamaparse=settings.processing.USE_LLAMAPARSE
                )
                markdown_content = parser.parse(str(file_path))

            if not markdown_content or not markdown_content.strip():
                print(f"[WARNING] No content extracted from {filename}")
                return False

            # Generate document metadata
            doc_metadata = self.metadata_generator.generate(
                file_path=file_path,
                folder_name=folder_name,
                page_metadata=page_metadata,
                parsed_content=markdown_content
            )

            # Save to processed/{domain}/{category}/
            self._save_processed_file(
                markdown_content=markdown_content,
                metadata=doc_metadata,
                category=category
            )

            self.stats["files_processed"] += 1
            print(f"[SUCCESS] Processed {filename} -> {doc_metadata['document_id']}.md")
            return True

        except ValueError as e:
            # Unsupported file type, skip silently
            print(f"[INFO] Skipping {filename}: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")
            raise

    def _clean_and_filter_content(self, content_path: Path, folder_name: str) -> Optional[str]:
        """
        Clean raw content.md and filter for quality.

        Args:
            content_path: Path to content.md
            folder_name: Folder name (for rejected file naming)

        Returns:
            Cleaned markdown if useful, None if filtered out
        """
        # Read raw content
        with open(content_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # Clean using domain-specific cleaner
        cleaned_content = self.cleaner.clean(raw_content)

        # Filter quality
        is_useful, reason = self.content_filter.is_useful(cleaned_content)

        if not is_useful:
            print(f"[FILTERED] content.md: {reason}")
            self.stats["files_filtered"] += 1

            # Track filter reasons
            if reason not in self.stats["filter_reasons"]:
                self.stats["filter_reasons"][reason] = 0
            self.stats["filter_reasons"][reason] += 1

            # Save to rejected folder for inspection
            self._save_rejected_file(cleaned_content, folder_name, reason)

            return None

        return cleaned_content

    def _load_page_metadata(self, metadata_path: Path) -> Dict:
        """Load page metadata from JSON file."""
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load metadata: {e}")
        return {}

    def _save_processed_file(
        self,
        markdown_content: str,
        metadata: Dict,
        category: str
    ):
        """
        Save processed file to flat structure.

        Structure:
            processed/{domain}/{category}/{document_id}.md
            processed/{domain}/{category}/{document_id}.json
        """
        # Create category directory
        category_dir = settings.paths.PROCESSED_DATA_DIR / self.domain / category
        category_dir.mkdir(parents=True, exist_ok=True)

        document_id = metadata["document_id"]

        # Save markdown
        md_path = category_dir / f"{document_id}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Save metadata
        json_path = category_dir / f"{document_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _save_rejected_file(self, content: str, folder_name: str, reason: str):
        """
        Save filtered content to rejected folder for inspection.

        Structure:
            processed/{domain}/.rejected/{folder_name}__content.md
            processed/{domain}/.rejected/{folder_name}__reason.txt
        """
        # Create rejected directory
        rejected_dir = settings.paths.PROCESSED_DATA_DIR / self.domain / ".rejected"
        rejected_dir.mkdir(parents=True, exist_ok=True)

        # Save content
        md_path = rejected_dir / f"{folder_name}__content.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Save reason
        reason_path = rejected_dir / f"{folder_name}__reason.txt"
        with open(reason_path, 'w', encoding='utf-8') as f:
            f.write(reason)

    def _print_stats(self):
        """Print final processing statistics."""
        print("\n" + "="*70)
        print("📊 PROCESSING COMPLETE - STATISTICS")
        print("="*70)
        print(f"   Folders processed:  {self.stats['folders_processed']}")
        print(f"   Folders skipped:    {self.stats['folders_skipped']}")
        print(f"   Files processed:    {self.stats['files_processed']}")
        print(f"   Files skipped:      {self.stats['files_skipped']} (already exists)")
        print(f"   Files filtered:     {self.stats['files_filtered']}")
        print(f"   Files failed:       {self.stats['files_failed']}")

        if self.stats["filter_reasons"]:
            print(f"\n   🚫 FILTER BREAKDOWN:")
            for reason, count in sorted(self.stats["filter_reasons"].items(), key=lambda x: -x[1]):
                print(f"      • {reason}: {count}")

        if self.stats["errors"]:
            print(f"\n   ⚠️  {len(self.stats['errors'])} ERRORS:")
            for err in self.stats["errors"][:10]:  # Show first 10
                print(f"      • {err['folder']}/{err['file']}: {err['error'][:60]}")
            if len(self.stats["errors"]) > 10:
                print(f"      ... and {len(self.stats['errors']) - 10} more")

        print("="*70 + "\n")


# Convenience functions
def process_domain(domain: str, categories: Optional[List[str]] = None):
    """
    Process a specific domain.

    Args:
        domain: Domain name (e.g., "daa.uit.edu.vn")
        categories: List of categories to process (None = use settings)

    Example:
        >>> from src.processing.pipeline_v2 import process_domain
        >>> process_domain("daa.uit.edu.vn", categories=["regulation", "curriculum"])
    """
    pipeline = ProcessingPipelineV2(domain=domain)
    pipeline.run(categories=categories)


def process_all_domains(categories: Optional[List[str]] = None):
    """
    Process all configured domains.

    Args:
        categories: List of categories to process (None = use settings)

    Example:
        >>> from src.processing.pipeline_v2 import process_all_domains
        >>> process_all_domains(categories=["regulation"])
    """
    for domain in settings.domains.START_URLS.keys():
        pipeline = ProcessingPipelineV2(domain=domain)
        pipeline.run(categories=categories)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run Processing Pipeline V2')
    parser.add_argument(
        '--domain', '-d',
        type=str,
        help='Process specific domain (e.g., daa.uit.edu.vn)'
    )
    parser.add_argument(
        '--categories', '-c',
        type=str,
        help='Comma-separated categories to process (e.g., regulation,curriculum)'
    )

    args = parser.parse_args()

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(',')]

    if args.domain:
        if args.domain not in settings.domains.START_URLS:
            print(f"[ERROR] Domain '{args.domain}' not configured")
        else:
            process_domain(args.domain, categories)
    else:
        process_all_domains(categories)
