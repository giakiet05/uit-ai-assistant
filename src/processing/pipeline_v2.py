"""
Processing Pipeline V2 - TWO-STAGE document processing wrapper.

This pipeline orchestrates both stages:
- Stage 1: Parse/Clean (pipeline_parse_clean.py)
- Stage 2: Metadata Generation (pipeline_metadata.py)

You can run stages independently or together via this wrapper.

RECOMMENDED USAGE:
    # Run both stages for new files
    python -m src.processing.pipeline_v2 --categories regulation

    # Re-generate metadata_generator only (cheaper, no parsing)
    python -m src.processing.pipeline_metadata --categories regulation --force

NOTE: Stage 1 (parse/clean) costs money (LlamaIndex parsing).
      Stage 2 (metadata_generator) can be re-run multiple times without re-parsing.
"""

from typing import List, Optional

from src.processing.pipeline_parse_clean import run_parse_clean
from src.processing.pipeline_metadata import run_metadata_generation


class ProcessingPipelineV2:
    """
    Wrapper pipeline that runs both Stage 1 (Parse/Clean) and Stage 2 (Metadata).

    For more control, use individual pipelines:
    - pipeline_parse_clean.py: Parse/clean raw files
    - pipeline_metadata.py: Generate metadata_generator from processed files
    """

    def __init__(self):
        """Initialize the processing pipeline wrapper."""
        pass

    def run(self,
            categories: Optional[List[str]] = None,
            force_parse: bool = False,
            force_metadata: bool = False,
            skip_stage1: bool = False,
            skip_stage2: bool = False):
        """
        Run both stages of the processing pipeline.

        Args:
            categories: List of specific categories to process (e.g., ["regulation"]).
                        If None, all categories will be processed.
            force_parse: If True, re-parse/clean existing files (Stage 1)
            force_metadata: If True, regenerate metadata_generator even if exists (Stage 2)
            skip_stage1: If True, skip parse/clean (only generate metadata_generator)
            skip_stage2: If True, skip metadata_generator generation (only parse/clean)
        """
        print("\n" + "="*70)
        print(f"🚀 PROCESSING PIPELINE V2 - TWO-STAGE WRAPPER")
        print("="*70 + "\n")

        # Stage 1: Parse & Clean
        if not skip_stage1:
            print("📋 Running Stage 1: Parse & Clean")
            print("-" * 70)
            run_parse_clean(categories=categories, force=force_parse)
        else:
            print("⏭️  Stage 1 SKIPPED (parse/clean)")
            print("-" * 70 + "\n")

        # Stage 2: Metadata Generation
        if not skip_stage2:
            print("\n📋 Running Stage 2: Metadata Generation")
            print("-" * 70)
            run_metadata_generation(categories=categories, force=force_metadata)
        else:
            print("⏭️  Stage 2 SKIPPED (metadata_generator generation)")
            print("-" * 70 + "\n")

        print("\n" + "="*70)
        print("✅ PIPELINE V2 COMPLETE")
        print("="*70 + "\n")


def run_processing(
    categories: Optional[List[str]] = None,
    force_parse: bool = False,
    force_metadata: bool = False,
    skip_stage1: bool = False,
    skip_stage2: bool = False
):
    """
    Convenience function to run the full processing pipeline.

    Args:
        categories: List of categories to process
        force_parse: Force re-parse/clean existing files
        force_metadata: Force regenerate metadata_generator
        skip_stage1: Skip parse/clean stage
        skip_stage2: Skip metadata_generator generation stage
    """
    pipeline = ProcessingPipelineV2()
    pipeline.run(
        categories=categories,
        force_parse=force_parse,
        force_metadata=force_metadata,
        skip_stage1=skip_stage1,
        skip_stage2=skip_stage2
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Run Processing Pipeline V2 (Two-Stage Wrapper)',
        epilog='''
Examples:
  # Run both stages for regulation category
  python -m src.processing.pipeline_v2 --categories regulation

  # Re-generate metadata_generator only (skip parsing)
  python -m src.processing.pipeline_v2 --categories regulation --skip-stage1 --force-metadata_generator

  # Parse/clean only (skip metadata_generator)
  python -m src.processing.pipeline_v2 --categories regulation --skip-stage2
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--categories', '-c',
        type=str,
        help='Comma-separated categories to process (e.g., regulation,curriculum)'
    )
    parser.add_argument(
        '--force-parse',
        action='store_true',
        help='Force re-parse/clean existing files (Stage 1)'
    )
    parser.add_argument(
        '--force-metadata_generator',
        action='store_true',
        help='Force regenerate metadata_generator even if exists (Stage 2)'
    )
    parser.add_argument(
        '--skip-stage1',
        action='store_true',
        help='Skip Stage 1 (parse/clean) - only generate metadata_generator'
    )
    parser.add_argument(
        '--skip-stage2',
        action='store_true',
        help='Skip Stage 2 (metadata_generator) - only parse/clean'
    )

    args = parser.parse_args()

    cats = args.categories.split(',') if args.categories else None

    run_processing(
        categories=cats,
        force_parse=args.force_parse,
        force_metadata=args.force_metadata,
        skip_stage1=args.skip_stage1,
        skip_stage2=args.skip_stage2
    )
