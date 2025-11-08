"""Pipeline command - Run full pipeline (crawl -> process)."""

import asyncio


def run_pipeline(args):
    """Handle pipeline command."""
    from src.crawler import crawl_all
    from src.processing.pipeline_v2 import process_all_domains

    async def run_full_pipeline():
        """Run crawl -> process pipeline."""
        print("\n" + "="*70)
        print("  FULL PIPELINE: CRAWL → PROCESS  ".center(70))
        print("="*70 + "\n")

        # Step 1: Crawl all domains
        print("🕷️  STEP 1: CRAWLING...")
        await crawl_all()

        # Step 2: Process all domains (categorize + clean + filter + parse)
        print("\n⚙️  STEP 2: PROCESSING...")
        process_all_domains()

        print("\n" + "="*70)
        print("  PIPELINE COMPLETE  ".center(70))
        print("="*70 + "\n")

    asyncio.run(run_full_pipeline())
