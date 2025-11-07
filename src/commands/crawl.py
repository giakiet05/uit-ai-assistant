"""Crawl command - Crawl websites for raw data."""

import asyncio


def run_crawl(args):
    """Handle crawl command."""
    from src.crawler import crawl_all, crawl_domain
    from src.config.settings import settings

    if args.domain:
        if args.domain not in settings.domains.START_URLS:
            print(f"[ERROR] Domain '{args.domain}' not configured in settings")
            return
        asyncio.run(crawl_domain(args.domain))
    else:
        asyncio.run(crawl_all())
