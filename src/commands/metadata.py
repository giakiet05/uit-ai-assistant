"""Metadata command - Stage 2: Generate metadata from processed files."""


def run_metadata(args):
    """Handle metadata command (Stage 2 only)."""
    from src.processing.pipeline_metadata import run_metadata_generation

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # Run Stage 2 only
    run_metadata_generation(
        categories=categories,
        force=args.force
    )
