"""Process command - Run processing pipeline v2 (two-stage wrapper)."""


def run_process(args):
    """Handle process command (runs both Stage 1 + Stage 2)."""
    from src.processing.pipeline_v2 import run_processing

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # Run both stages (parse/clean + metadata)
    run_processing(
        categories=categories,
        force_parse=getattr(args, 'force_parse', False),
        force_metadata=getattr(args, 'force_metadata', False),
        skip_stage1=getattr(args, 'skip_stage1', False),
        skip_stage2=getattr(args, 'skip_stage2', False)
    )
