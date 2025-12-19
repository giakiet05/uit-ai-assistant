"""
Crawler implementation for daa.uit.edu.vn.
"""
from .filters.daa_filter import DaaUrlFilter
from crawl4ai import (
    AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig,
    BestFirstCrawlingStrategy, FilterChain, DomainFilter
)

from src.config import settings

RAW_DATA_DIR = settings.paths.RAW_DATA_DIR
MAX_PAGES_PER_DOMAIN = settings.env.MAX_PAGES_PER_DOMAIN

from .base_crawler import BaseCrawler
from .crawler_helper import (
    create_or_get_folder_for_url, download_file, extract_title_from_content,
    filter_downloadable_links, save_crawled_data, should_exclude_node_url
)
from src.utils.url_utils import make_absolute_url


class DaaCrawler(BaseCrawler):
    """Crawler specifically for 'daa.uit.edu.vn'."""

    async def crawl(self):
        """Executes the crawling logic for DAA website."""
        print(f"Initializing DAA crawler for domain: {self.domain}")

        url_filter = DaaUrlFilter()

        def _is_important(url: str) -> bool:
            return url_filter.is_important(url)

        def _get_priority(url: str) -> float:
            # get_priority trả về int 0-100 theo code của bạn
            try:
                return float(url_filter.get_priority(url) or 0)
            except Exception:
                return 50.0

        def custom_url_scorer(url: str) -> float:
            """Trả về score trong [0.0, 1.0] dựa trên filter.get_priority."""
            try:
                if not _is_important(url):
                    return 0.0
                p = _get_priority(url)
                # Clip defensively
                if p < 0:
                    p = 0.0
                if p > 100:
                    p = 100.0
                return p / 100.0
            except Exception as e:
                print(f"[WARN] url_scorer error for {url}: {e}")
                return 0.5

        filter_chain = FilterChain([
            DomainFilter(allowed_domains=[self.domain]),
        ])

        strategy = BestFirstCrawlingStrategy(
            max_depth=3,  # bạn có thể điều chỉnh về 2 nếu muốn ít sâu hơn
            include_external=False,
            url_scorer=custom_url_scorer,
            # --- FIX: Use settings.crawler.MAX_PAGES_PER_DOMAIN ---
            max_pages=settings.crawler.MAX_PAGES_PER_DOMAIN,
            filter_chain=filter_chain,
        )
        browser_config = BrowserConfig(verbose=True)
        run_config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            word_count_threshold=10,
            excluded_tags=['form', 'header', 'nav', 'footer', 'aside', 'menu'],
            exclude_external_links=True,
            process_iframes=True,
            remove_overlay_elements=True,
            cache_mode=CacheMode.ENABLED,
            delay_before_return_html=2.0,
        )

        crawled_pages = []
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun(url=self.start_url, config=run_config)
            print(f"Deep crawl completed! Found {len(results)} pages.")

            for i, result in enumerate(results):
                if not result.success:
                    print(f"[ERROR] Failed to crawl: {result.url} - {result.error_message}")
                    continue
                if should_exclude_node_url(result.url):
                    print(f"[INFO] Skipped node url: {result.url}")
                    continue
                if not (result.markdown and result.markdown.strip()):
                    print(f"[INFO] No content found: {result.url}")
                    continue
                
                if not url_filter.is_important(result.url):
                    print(f"[SKIP] Unimportant URL: {result.url}")
                    continue
                title = extract_title_from_content(result.markdown) or f"Page {i + 1}"
                folder_saved = save_crawled_data(
                    url=result.url,
                    title=title,
                    content=result.markdown,
                    source_urls=[self.start_url, result.url]
                )

                downloaded_files_count = 0
                if folder_saved:
                    # --- FIX: Use settings.paths.RAW_DATA_DIR ---
                    page_folder = create_or_get_folder_for_url(result.url, str(settings.paths.RAW_DATA_DIR))
                    downloadable_links = filter_downloadable_links(result.links["internal"])
                    for file_url in downloadable_links:
                        absolute_file_url = make_absolute_url(file_url, result.url)
                        if download_file(absolute_file_url, page_folder):
                            downloaded_files_count += 1

                crawled_pages.append({
                    'url': result.url, 'title': title, 'downloaded_files': downloaded_files_count,
                    'was_updated': folder_saved is not None
                })
                status_text = "[SAVED]" if folder_saved else "[SKIPPED]"
                print(f"{status_text} Processed page: {title[:50]}... (Downloaded {downloaded_files_count} files)")

        print(f"\n--- DAA Crawl Summary: Total pages processed: {len(crawled_pages)} ---\n")
        return crawled_pages
