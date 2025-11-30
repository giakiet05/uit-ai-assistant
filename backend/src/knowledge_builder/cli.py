"""
UIT Agent CLI - Command Line Interface for UIT AI Agent Backend.

Usage:
    ua <command> [options]

Commands:
    crawl        - Crawl websites for raw data
    parse        - Parse attachments to markdown (legacy)
    clean        - Stage 1: Parse & clean raw files (costs money)
    metadata_generator     - Stage 2: Generate metadata_generator from processed files (cheap, can re-run)
    process      - Run both stages (parse/clean + metadata_generator)
    fix-markdown - Fix markdown structure using Gemini LLM
    index        - Build vector store index from processed documents
    pipeline     - Run full pipeline (crawl -> process)

Examples:
    ua crawl --domain daa.uit.edu.vn
    ua clean --categories regulation,curriculum
    ua metadata_generator --categories regulation,curriculum --force
    ua process --categories regulation,curriculum
    ua index --categories regulation,curriculum
"""

import argparse
import sys


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ua",
        description="UIT Agent CLI - Data pipeline management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ua crawl --domain daa.uit.edu.vn
  ua clean --categories regulation,curriculum
  ua metadata_generator --categories regulation --force
  ua process --categories regulation
  ua index --categories regulation,curriculum
  ua pipeline
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ===== CRAWL =====
    crawl_parser = subparsers.add_parser(
        "crawl",
        help="Crawl websites for raw data"
    )
    crawl_parser.add_argument(
        "--domain", "-d",
        help="Specific domain to crawl (default: all configured domains)"
    )

    # ===== PARSE (LEGACY) =====
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse attachments to markdown (legacy parser)"
    )
    parse_parser.add_argument(
        "--domain", "-d",
        help="Specific domain to parse (default: all)"
    )
    parse_parser.add_argument(
        "--folder", "-f",
        help="Specific folder path to parse"
    )

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
        "metadata_generator",
        help="Stage 2: Generate metadata_generator from processed files (cheap, can re-run)"
    )
    metadata_parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories to process (e.g., regulation,curriculum)"
    )
    metadata_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force regenerate metadata_generator even if exists"
    )

    # ===== PROCESS (V2 - BOTH STAGES) =====
    process_parser = subparsers.add_parser(
        "process",
        help="Run both stages (parse/clean + metadata_generator)"
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
        "--force-metadata_generator",
        action="store_true",
        help="Force regenerate metadata_generator even if exists (Stage 2)"
    )
    process_parser.add_argument(
        "--skip-stage1",
        action="store_true",
        help="Skip Stage 1 (parse/clean) - only generate metadata_generator"
    )
    process_parser.add_argument(
        "--skip-stage2",
        action="store_true",
        help="Skip Stage 2 (metadata_generator) - only parse/clean"
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

    # ===== INDEX =====
    index_parser = subparsers.add_parser(
        "index",
        help="Build vector store index from processed documents"
    )
    index_parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories (e.g., regulation,curriculum)"
    )

    # ===== PIPELINE (FULL) =====
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run full pipeline (crawl -> clean -> parse)"
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handlers
    try:
        if args.command == "crawl":
            from .commands.crawl import run_crawl
            run_crawl(args)
        elif args.command == "clean":
            from .commands import run_clean
            run_clean(args)
        elif args.command == "metadata_generator":
            from .commands.metadata import run_metadata
            run_metadata(args)
        elif args.command == "process":
            from .commands.process import run_process
            run_process(args)
        elif args.command == "fix-markdown":
            from .commands.fix_markdown import fix_markdown_command
            fix_markdown_command(
                category=args.category,
                file_path=args.file,
                dry_run=args.dry_run
            )
        elif args.command == "index":
            from .commands.index import run_index
            run_index(args)
        elif args.command == "pipeline":
            from .commands import run_pipeline
            run_pipeline(args)
    except KeyboardInterrupt:
        print("\n[INFO] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
