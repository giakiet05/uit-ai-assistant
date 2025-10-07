import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, BFSDeepCrawlStrategy, \
    LXMLWebScrapingStrategy, BestFirstCrawlingStrategy, KeywordRelevanceScorer

# --- Configuration Paths ---
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
RAW_DATA_DIR = os.path.join(ROOT_DIR, 'data', 'raw', 'daa')
URL = "https://daa.uit.edu.vn"

os.makedirs(RAW_DATA_DIR, exist_ok=True)


async def simple_crawl_daa():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        # Content filtering
        word_count_threshold=10,
        excluded_tags=['form', 'header'],
        exclude_external_links=True,

        # Content processing
        process_iframes=True,
        remove_overlay_elements=True,

        # Cache control
        cache_mode=CacheMode.ENABLED  # Use cache if available
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=URL,
            config=run_config
        )

        if result.success:
            # Print clean content
            print("Content:", result.markdown[:1000])  # First 500 chars

            # Process images
            for image in result.media["images"]:
                print(f"Found image: {image['src']}")

            # Process links
            for link in result.links["internal"]:
                print(f"Internal link: {link['href']}")

        else:
            print(f"Crawl failed: {result.error_message}")

async def deep_crawl_daa():
    # Create a scorer
    scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    # Configure the strategy
    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        include_external=False,
        url_scorer=scorer,
        max_pages=25,  # Maximum number of pages to crawl (optional)
    )

    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=URL, config=config)

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        for result in results[:3]:  # Show first 3 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}"

                  )
async def scorer_crawl():
    # Create a keyword relevance scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7  # Importance of this scorer (0.0 to 1.0)
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            url_scorer=keyword_scorer
        ),
        stream=True  # Recommended with BestFirstCrawling
    )

    # Results will come in order of relevance score
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://example.com", config=config):
            score = result.metadata.get("score", 0)
            print(f"Score: {score:.2f} | {result.url}")
