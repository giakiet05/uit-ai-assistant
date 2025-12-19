"""
UIT Knowledge Builder CLI - Build and manage knowledge base for UIT AI Assistant.

Usage:
    ukb <command> [options]

Commands:
    clean        - Stage 1: Parse & clean raw files (costs money)
    metadata     - Stage 2: Generate metadata from processed files (cheap, can re-run)
    process      - Run both stages (parse/clean + metadata)
    fix-markdown - Fix markdown structure using Gemini LLM
    reparse-file - Re-parse a single PDF file
    index        - Build vector store index from processed documents

Examples:
    ukb clean --categories regulation,curriculum
    ukb metadata --categories regulation,curriculum --force
    ukb process --categories regulation,curriculum
    ukb fix-markdown --category regulation
    ukb index --categories regulation,curriculum
"""

import argparse
import sys


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

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handlers
    try:
        if args.command == "clean":
            from src.commands.clean import run_clean
            run_clean(args)
        elif args.command == "metadata":
            from src.commands.metadata import run_metadata
            run_metadata(args)
        elif args.command == "process":
            from src.commands.process import run_process
            run_process(args)
        elif args.command == "fix-markdown":
            from src.commands.fix_markdown import fix_markdown_command
            fix_markdown_command(
                category=args.category,
                file_path=args.file,
                dry_run=args.dry_run
            )
        elif args.command == "reparse-file":
            from src.commands.reparse_file import reparse_file
            reparse_file(args.filename)
        elif args.command == "index":
            from src.commands.index import run_index
            run_index(args)
    except KeyboardInterrupt:
        print("\n[INFO] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
