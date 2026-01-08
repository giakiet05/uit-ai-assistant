"""
UIT Knowledge Builder CLI - Build and manage knowledge base for UIT AI Assistant.

Usage:
    ukb <command> [options]

Commands (New Stage-Based Pipeline):
    pipeline     - Run processing/indexing pipelines
    stage        - Run a specific stage
    status       - Show pipeline status
    migrate      - Migrate from old structure to stages/

Legacy Commands (Deprecated):
    clean        - Use 'ukb pipeline run' instead
    metadata     - Use 'ukb stage metadata' instead
    process      - Use 'ukb pipeline run' instead
    index        - Use 'ukb pipeline run --indexing-only' instead

Examples:
    ukb pipeline run --category regulation
    ukb pipeline run --file data/stages/regulation/790-qd-dhcntt
    ukb stage parse --category regulation
    ukb status --category regulation
    ukb migrate --categories regulation
"""

import argparse
import sys
from pathlib import Path

# Add src to sys.path for imports to work
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ukb",
        description="UIT Knowledge Builder - Build and manage knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ukb clean --categories regulation,curriculum
  ukb metadata --categories regulation --force
  ukb process --categories regulation
  ukb fix-markdown --category regulation
  ukb index --categories regulation,curriculum
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ===== CLEAN (STAGE 1) =====
    clean_parser = subparsers.add_parser(
        "clean",
        help="Stage 1: Parse & clean raw files (costs money via LlamaParse)"
    )
    clean_parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories to process (e.g., regulation,curriculum)"
    )
    clean_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-process existing files"
    )

    # ===== METADATA (STAGE 2) =====
    metadata_parser = subparsers.add_parser(
        "metadata",
        help="Stage 2: Generate metadata from processed files (cheap, can re-run)"
    )
    metadata_parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories to process (e.g., regulation,curriculum)"
    )
    metadata_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force regenerate metadata even if exists"
    )

    # ===== PROCESS (BOTH STAGES) =====
    process_parser = subparsers.add_parser(
        "process",
        help="Run both stages (parse/clean + metadata)"
    )
    process_parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories to process (e.g., regulation,curriculum)"
    )
    process_parser.add_argument(
        "--force-parse",
        action="store_true",
        help="Force re-parse/clean existing files (Stage 1)"
    )
    process_parser.add_argument(
        "--force-metadata",
        action="store_true",
        help="Force regenerate metadata even if exists (Stage 2)"
    )
    process_parser.add_argument(
        "--skip-stage1",
        action="store_true",
        help="Skip Stage 1 (parse/clean) - only generate metadata"
    )
    process_parser.add_argument(
        "--skip-stage2",
        action="store_true",
        help="Skip Stage 2 (metadata) - only parse/clean"
    )

    # ===== FIX-MARKDOWN =====
    fix_markdown_parser = subparsers.add_parser(
        "fix-markdown",
        help="Fix markdown structure using Gemini LLM"
    )
    fix_markdown_parser.add_argument(
        "--category", "-c",
        help="Category to fix (regulation, curriculum, etc.)"
    )
    fix_markdown_parser.add_argument(
        "--file", "-f",
        help="Single file to fix (overrides --category)"
    )
    fix_markdown_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving"
    )

    # ===== REPARSE-FILE =====
    reparse_parser = subparsers.add_parser(
        "reparse-file",
        help="Re-parse a single PDF file"
    )
    reparse_parser.add_argument(
        "filename",
        help="PDF filename or ID (e.g., '547' or '547.pdf')"
    )

    # ===== INDEX =====
    index_parser = subparsers.add_parser(
        "index",
        help="Build vector store index from processed documents"
    )
    index_parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories (e.g., regulation,curriculum)"
    )
    index_parser.add_argument(
        "--file", "-f",
        help="Path to single file to index (e.g., data/processed/regulation/file.md)"
    )

    # ===== MIGRATE =====
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate from processed/ to stages/ structure (one-time)"
    )
    migrate_parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories to migrate (default: all)"
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes"
    )

    # ===== PIPELINE (NEW) =====
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run processing/indexing pipelines"
    )
    pipeline_subparsers = pipeline_parser.add_subparsers(dest="pipeline_command", help="Pipeline commands")

    # pipeline run
    pipeline_run_parser = pipeline_subparsers.add_parser(
        "run",
        help="Run full pipeline or specific range"
    )
    pipeline_run_parser.add_argument(
        "--category", "-c",
        help="Category to process (e.g., regulation)"
    )
    pipeline_run_parser.add_argument(
        "--file", "-f",
        help="Single document directory to process"
    )
    pipeline_run_parser.add_argument(
        "--from-stage",
        help="Starting stage (e.g., parse, clean, chunk)"
    )
    pipeline_run_parser.add_argument(
        "--to-stage",
        help="Ending stage (inclusive)"
    )
    pipeline_run_parser.add_argument(
        "--force",
        action="store_true",
        help="Force rerun all stages"
    )
    pipeline_run_parser.add_argument(
        "--skip-fix-markdown",
        action="store_true",
        help="Skip fix-markdown stage (save cost)"
    )
    pipeline_run_parser.add_argument(
        "--processing-only",
        action="store_true",
        help="Only run processing pipeline (parse → metadata)"
    )
    pipeline_run_parser.add_argument(
        "--indexing-only",
        action="store_true",
        help="Only run indexing pipeline (chunk → embed-index)"
    )

    # ===== STAGE (NEW) =====
    stage_parser = subparsers.add_parser(
        "stage",
        help="Run a specific stage"
    )
    stage_parser.add_argument(
        "stage",
        help="Stage name (parse, clean, normalize, filter, fix-markdown, metadata, chunk, embed-index)"
    )
    stage_parser.add_argument(
        "--category", "-c",
        help="Category to process"
    )
    stage_parser.add_argument(
        "--file", "-f",
        help="Single document directory to process"
    )
    stage_parser.add_argument(
        "--force",
        action="store_true",
        help="Force rerun stage"
    )

    # ===== STATUS (NEW) =====
    status_parser = subparsers.add_parser(
        "status",
        help="Show pipeline status"
    )
    status_parser.add_argument(
        "--category", "-c",
        help="Category to show status for"
    )
    status_parser.add_argument(
        "--file", "-f",
        help="Single document directory to show status for"
    )
    status_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed stage information"
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handlers
    try:
        # New stage-based commands
        if args.command == "pipeline":
            if args.pipeline_command == "run":
                from commands.pipeline import run_pipeline
                run_pipeline(args)
            else:
                pipeline_parser.print_help()

        elif args.command == "stage":
            from commands.stage import run_stage
            run_stage(args)

        elif args.command == "status":
            from commands.status import run_status
            run_status(args)

        elif args.command == "migrate":
            from commands.migrate import run_migrate
            run_migrate(args)

        # Legacy commands (deprecated)
        elif args.command == "clean":
            print("[WARNING] 'clean' command is deprecated. Use 'ukb pipeline run --processing-only' instead")
            from commands.clean import run_clean
            run_clean(args)

        elif args.command == "metadata":
            print("[WARNING] 'metadata' command is deprecated. Use 'ukb stage metadata' instead")
            from commands.metadata import run_metadata
            run_metadata(args)

        elif args.command == "process":
            print("[WARNING] 'process' command is deprecated. Use 'ukb pipeline run' instead")
            from commands.process import run_process
            run_process(args)

        elif args.command == "fix-markdown":
            print("[WARNING] 'fix-markdown' command is deprecated. Use 'ukb stage fix-markdown' instead")
            from commands.fix_markdown import fix_markdown_command
            fix_markdown_command(
                category=args.category,
                file_path=args.file,
                dry_run=args.dry_run
            )

        elif args.command == "reparse-file":
            print("[WARNING] 'reparse-file' command is deprecated. Use 'ukb stage parse' instead")
            from commands.reparse_file import reparse_file
            reparse_file(args.filename)

        elif args.command == "index":
            print("[WARNING] 'index' command is deprecated. Use 'ukb pipeline run --indexing-only' instead")
            from commands.index import run_index
            run_index(args)

    except KeyboardInterrupt:
        print("\n[INFO] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        import traceback
        print(f"[ERROR] {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
