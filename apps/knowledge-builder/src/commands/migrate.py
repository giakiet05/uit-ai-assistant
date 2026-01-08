"""
Migration command - Migrate processed/ to stages/ structure.

One-time migration from legacy flat structure to stage-based structure.
"""

import shutil
from pathlib import Path
from typing import Optional, List
from config.settings import settings
from pipeline.core.pipeline_state import PipelineState


def run_migrate(args):
    """
    Handle migrate command.

    Migrates from legacy structure:
        data/processed/{category}/{doc_id}.md
        data/processed/{category}/{doc_id}.json

    To new stage-based structure:
        data/stages/{category}/{doc_id}/
            ├── 05-fixed.md (final processed output)
            ├── metadata.json
            └── .pipeline.json (fake history)

    Args:
        args: Command arguments
    """
    categories = None
    if hasattr(args, 'categories') and args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    dry_run = getattr(args, 'dry_run', False)

    print("\n" + "="*70)
    print(" MIGRATION: processed/ -> stages/")
    if dry_run:
        print("   [DRY RUN MODE - No changes will be made]")
    print("="*70 + "\n")

    migrator = LegacyMigrator(dry_run=dry_run)
    migrator.migrate(categories=categories)


class LegacyMigrator:
    """Migrate from legacy processed/ structure to stages/ structure."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize migrator.

        Args:
            dry_run: If True, only print what would be done
        """
        self.dry_run = dry_run
        self.processed_dir = settings.paths.PROCESSED_DATA_DIR
        self.stages_dir = settings.paths.STAGES_DIR

        self.stats = {
            "documents_migrated": 0,
            "documents_skipped": 0,
            "errors": []
        }

    def migrate(self, categories: Optional[List[str]] = None):
        """
        Run migration.

        Args:
            categories: List of categories to migrate (None = all)
        """
        if not self.processed_dir.exists():
            print(f"[ERROR] processed/ directory not found: {self.processed_dir}")
            print("[INFO] Nothing to migrate.")
            return

        # Find categories
        if categories:
            category_dirs = [
                self.processed_dir / cat
                for cat in categories
                if (self.processed_dir / cat).is_dir()
            ]
        else:
            category_dirs = [d for d in self.processed_dir.iterdir() if d.is_dir()]

        if not category_dirs:
            print("[INFO] No categories found to migrate.")
            return

        print(f" Found {len(category_dirs)} categories: {[d.name for d in category_dirs]}\n")

        # Migrate each category
        for category_dir in category_dirs:
            category = category_dir.name
            self._migrate_category(category)

        self._print_stats()

        if not self.dry_run:
            print("\n Next steps:")
            print("   1. Verify migration: ukb status --all")
            print("   2. Test new pipeline with migrated data")
            print("   3. Delete processed/ folder: rm -rf data/processed")

    def _migrate_category(self, category: str):
        """
        Migrate a single category.

        Args:
            category: Category name
        """
        print(f"\n{'='*70}")
        print(f" MIGRATING CATEGORY: {category.upper()}")
        print(f"{'='*70}\n")

        category_dir = self.processed_dir / category
        md_files = list(category_dir.glob("*.md"))

        print(f"[INFO] Found {len(md_files)} documents in {category}\n")

        for idx, md_file in enumerate(md_files, 1):
            print(f"[{idx}/{len(md_files)}] ", end="")
            self._migrate_document(category, md_file)

    def _migrate_document(self, category: str, md_file: Path):
        """
        Migrate a single document.

        Args:
            category: Category name
            md_file: Path to .md file
        """
        doc_id = md_file.stem

        # Check if already migrated
        stage_dir = self.stages_dir / category / doc_id
        if stage_dir.exists() and not self.dry_run:
            print(f"[SKIP] {doc_id}: Already migrated")
            self.stats["documents_skipped"] += 1
            return

        try:
            if self.dry_run:
                print(f"[DRY RUN] Would migrate: {doc_id}")
                print(f"   -> Create: {stage_dir}")
                print(f"   -> Copy: {md_file.name} -> 05-fixed.md")

                json_file = md_file.with_suffix('.json')
                if json_file.exists():
                    print(f"   -> Copy: {json_file.name} -> metadata.json")

                print(f"   -> Create: .pipeline.json (fake history)")
                self.stats["documents_migrated"] += 1
                return

            # Create stage directory
            stage_dir.mkdir(parents=True, exist_ok=True)

            # Copy final markdown
            final_md = stage_dir / "05-fixed.md"
            shutil.copy(md_file, final_md)
            print(f"[MIGRATE] {doc_id}: Copied {md_file.name} -> 05-fixed.md")

            # Copy metadata if exists
            json_file = md_file.with_suffix('.json')
            has_metadata = False
            if json_file.exists():
                metadata_file = stage_dir / "metadata.json"
                shutil.copy(json_file, metadata_file)
                print(f"   -> Copied {json_file.name} -> metadata.json")
                has_metadata = True

            # Create fake pipeline state
            self._create_pipeline_state(category, doc_id, has_metadata)
            print(f"   -> Created .pipeline.json (fake history)")

            self.stats["documents_migrated"] += 1
            print(f"    Migration complete")

        except Exception as e:
            print(f"    [ERROR] Failed to migrate {doc_id}: {e}")
            self.stats["errors"].append({
                "document": doc_id,
                "category": category,
                "error": str(e)
            })

    def _create_pipeline_state(self, category: str, doc_id: str, has_metadata: bool):
        """
        Create fake pipeline state for migrated document.

        Args:
            category: Category name
            doc_id: Document ID
            has_metadata: Whether metadata.json exists
        """
        state = PipelineState(doc_id, category)

        # Mark all stages as completed (fake history)
        # We don't know the actual history, so mark everything as done
        state.add_stage(
            "parse",
            PipelineState.STATUS_COMPLETED,
            output_file="05-fixed.md"
        )

        state.add_stage(
            "clean",
            PipelineState.STATUS_COMPLETED,
            output_file="05-fixed.md"
        )

        state.add_stage(
            "normalize",
            PipelineState.STATUS_SKIPPED,  # Not run in legacy pipeline
        )

        state.add_stage(
            "filter",
            PipelineState.STATUS_COMPLETED,
            output_file="05-fixed.md"
        )

        state.add_stage(
            "fix-markdown",
            PipelineState.STATUS_COMPLETED,
            output_file="05-fixed.md"
        )

        if has_metadata:
            state.add_stage(
                "metadata",
                PipelineState.STATUS_COMPLETED
            )
        else:
            state.add_stage(
                "metadata",
                PipelineState.STATUS_PENDING
            )

        # Set migrated flag
        state.migrated_from_legacy = True
        state.final_output = "05-fixed.md"
        state.current_stage = "metadata" if has_metadata else "fix-markdown"

        # Save
        state.save()

    def _print_stats(self):
        """Print migration statistics."""
        print("\n" + "="*70)
        print(" MIGRATION COMPLETE - STATISTICS")
        print("="*70)
        print(f"   Documents migrated:  {self.stats['documents_migrated']}")
        print(f"   Documents skipped:   {self.stats['documents_skipped']}")
        print(f"   Errors:              {len(self.stats['errors'])}")

        if self.stats["errors"]:
            print(f"\n     {len(self.stats['errors'])} ERRORS:")
            for err in self.stats["errors"][:10]:
                print(f"      • {err['document']}: {str(err['error'])[:60]}")
            if len(self.stats["errors"]) > 10:
                print(f"      ... and {len(self.stats['errors']) - 10} more")

        print("="*70 + "\n")
