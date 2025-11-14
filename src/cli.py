"""
UIT Agent CLI - Command Line Interface for UIT AI Agent Backend.

Usage:
    ua <command> [options]

Commands:
    crawl     - Crawl websites for raw data
    parse     - Parse attachments to markdown (legacy)
    clean     - Stage 1: Parse & clean raw files (costs money)
    metadata  - Stage 2: Generate metadata from processed files (cheap, can re-run)
    process   - Run both stages (parse/clean + metadata)
    build     - Build vector store index
    pipeline  - Run full pipeline (crawl -> process)

Examples:
    ua crawl --domain daa.uit.edu.vn
    ua clean --categories regulation,curriculum
    ua metadata --categories regulation,curriculum --force
    ua process --categories regulation,curriculum
    ua build --categories regulation,curriculum
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
  ua metadata --categories regulation --force
  ua process --categories regulation
  ua build --categories regulation,curriculum
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

    # ===== PROCESS (V2 - BOTH STAGES) =====
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

    # ===== BUILD =====
    build_parser = subparsers.add_parser(
        "build",
        help="Build vector store index (multi-collection, category-based)"
    )
    build_parser.add_argument(
        "--domain", "-d",
        help="Specific domain to build (default: all)"
    )
    build_parser.add_argument(
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
            from src.commands.crawl import run_crawl
            run_crawl(args)
        elif args.command == "clean":
            from src.commands.clean import run_clean
            run_clean(args)
        elif args.command == "metadata":
            from src.commands.metadata import run_metadata
            run_metadata(args)
        elif args.command == "process":
            from src.commands.process import run_process
            run_process(args)
        elif args.command == "build":
            from src.commands.build import run_build
            run_build(args)
        elif args.command == "pipeline":
            from src.commands.pipeline import run_pipeline
            run_pipeline(args)
    except KeyboardInterrupt:
        print("\n[INFO] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
