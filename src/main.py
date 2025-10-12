import asyncio

from src.crawler.crawler_core import crawl_all, simple_crawl_daa
if __name__ == "__main__":
    asyncio.run(crawl_all())
