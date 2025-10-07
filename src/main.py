import asyncio

from src.crawler.crawler_examples import deep_crawl_daa, scorer_crawl, simple_crawl_daa

if __name__ == "__main__":
    asyncio.run(simple_crawl_daa())
