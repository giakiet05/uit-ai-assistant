"""Clean command - Stage 1: Parse & clean raw files."""


def run_clean(args):
    """Handle clean command (Stage 1 only)."""
    from src.processing.pipeline_parse_clean import run_parse_clean

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # Run Stage 1 only
    run_parse_clean(
        categories=categories,
        force=args.force
    )
