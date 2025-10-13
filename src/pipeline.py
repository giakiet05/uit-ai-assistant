"""
Main data processing pipeline that chains crawling and cleaning.
"""
import asyncio

from src.config import START_URLS
from src.crawler import crawl_all
from src.preprocessing import CleanerFactory, clean_all

async def run_pipeline():
    """
    Executes the full data pipeline:
    1. Crawls all configured websites to fetch raw data.
    2. Cleans the raw data and stores it in the processed directory.
    """
    # --- STEP 1: CRAWLING ---
    print("="*50)
    print("🚀 STARTING PIPELINE: STEP 1 - CRAWLING")
    print("="*50)
    await crawl_all()
    print("\n" + "="*50)
    print("✅ FINISHED PIPELINE: STEP 1 - CRAWLING")
    print("="*50 + "\n")

    # --- STEP 2: CLEANING ---
    # The cleaning logic is now self-contained in the clean_all function
    # from the cleaner_core module, which the preprocessing package exposes.
    await clean_all()

if __name__ == "__main__":
    print("Running the full data processing pipeline...")
    asyncio.run(run_pipeline())
    print("Pipeline execution complete.")
