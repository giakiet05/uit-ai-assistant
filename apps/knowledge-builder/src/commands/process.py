"""Process command - Run both processing stages."""


def run_process(args):
    """Handle process command (runs both Stage 1 + Stage 2)."""
    from ..processing.pipelines.parse_clean_pipeline import run_parse_clean
    from ..processing.pipelines.metadata_pipeline import run_metadata_generation

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # Stage 1: Parse & Clean
    if not getattr(args, 'skip_stage1', False):
        print("\n" + "="*70)
        print("🚀 STAGE 1: PARSE & CLEAN")
        print("="*70 + "\n")
        run_parse_clean(
            categories=categories,
            force=getattr(args, 'force_parse', False)
        )
    else:
        print("⏭️  Stage 1 SKIPPED (parse/clean)\n")

    # Stage 2: Metadata Generation
    if not getattr(args, 'skip_stage2', False):
        print("\n" + "="*70)
        print("🚀 STAGE 2: METADATA GENERATION")
        print("="*70 + "\n")
        run_metadata_generation(
            categories=categories,
            force=getattr(args, 'force_metadata', False)
        )
    else:
        print("⏭️  Stage 2 SKIPPED (metadata generation)\n")

    print("\n" + "="*70)
    print("✅ PROCESSING COMPLETE")
    print("="*70 + "\n")
