import os
import re

from crawl4ai import KeywordRelevanceScorer, BrowserConfig, CrawlerRunConfig, CacheMode, AsyncWebCrawler, \
    BestFirstCrawlingStrategy, FilterChain, DomainFilter

from src.crawler.crawler_cleaner import clean_daa_content
from src.crawler.crawler_config import downloads_path, RAW_DATA_DIR, URL_GROUPS
from src.crawler.crawler_helper import extract_title_from_content, save_crawled_data, download_file, create_folder_for_url, filter_downloadable_links

os.makedirs(downloads_path, exist_ok=True)
os.makedirs(RAW_DATA_DIR, exist_ok=True)


def should_exclude_node_url(url: str) -> bool:
    """Check if URL should be excluded (node/id format)"""
    return bool(re.search(r'/node/\d+', url))


async def simple_crawl_daa(url: str):
    browser_config = BrowserConfig(
        verbose=True,
        accept_downloads=True,
        downloads_path=downloads_path)

    run_config = CrawlerRunConfig(
        # Content filtering - Strategy 2: Enhanced filtering
        word_count_threshold=10,
        excluded_tags=['form', 'header', 'nav', 'footer', 'aside', 'menu'],
        exclude_external_links=True,

        # Content processing
        process_iframes=True,
        remove_overlay_elements=True,

        # Cache control
        cache_mode=CacheMode.ENABLED,

        # Add delay to allow downloads to start
        delay_before_return_html=2.0,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )

        if result.success:
            # Save raw content without cleaning
            raw_content = result.markdown or result.html or ""

            print("Content preview:", raw_content[:500])

            # Process images
            for image in result.media["images"]:
                print(f"Found image: {image['src']}")

            # Process links
            for link in result.links["internal"]:
                print(f"Internal link: {link['href']}")

            # Extract title from raw content or use default
            title = extract_title_from_content(raw_content) or "Thông báo chung"
            save_crawled_data(
                url=url,
                title=title,
                content=raw_content,  # Save raw content
                source_urls=["https://daa.uit.edu.vn/", url]
            )

        else:
            print(f"Crawl failed: {result.error_message}")


async def crawl_daa_url(url: str):
    # Setup scorer for announcement pages and pagination
    scorer = KeywordRelevanceScorer(
        keywords=[
            "thong-bao", "page", "trang",
            "lich-thi", "quy-dinh", "tot-nghiep", "hoc-tap", "ke-hoach", "ban-hanh", "cap-nhat", "ky-thi", "khao-sat",
            "2022", "2023", "2024", "2025"  # Recent years
        ],
        weight=0.8
    )

    # Create a chain of filters
    filter_chain = FilterChain([
        DomainFilter(
            allowed_domains=["daa.uit.edu.vn"],
        ),
    ])

    # Setup deep crawl strategy that follows pagination
    strategy = BestFirstCrawlingStrategy(
        max_depth=2,  # Level 1: main page, Level 2: pagination pages + individual announcements
        include_external=False,
        url_scorer=scorer,
        max_pages=1000,  # Limit total pages to crawl
        filter_chain=filter_chain,
    )

    browser_config = BrowserConfig(
        verbose=True,
        accept_downloads=True,
        downloads_path=downloads_path
    )

    run_config = CrawlerRunConfig(
        # Deep crawling with pagination
        deep_crawl_strategy=strategy,

        # Content filtering
        word_count_threshold=10,
        excluded_tags=['form', 'header', 'nav', 'footer', 'aside', 'menu'],
        exclude_external_links=True,

        # Content processing
        process_iframes=True,
        remove_overlay_elements=True,

        # Cache control
        cache_mode=CacheMode.ENABLED,
        delay_before_return_html=2.0,

    )

    crawled_announcements = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun(url=url, config=run_config)

        print(f"Deep crawl completed! Found {len(results)} pages")

        for i, result in enumerate(results):
            if result.success:
                # Skip node/id urls (mấy cái học bù, nghỉ học)
                if should_exclude_node_url(result.url):
                    print(f"✗ Skipped node url: {result.url}")
                    continue

                if result.markdown and result.markdown.strip():  # Only save if there's actual content
                    title = extract_title_from_content(result.markdown) or f"Page {i + 1}"

                    # Check if content has changed before processing files
                    folder_saved = save_crawled_data(
                        url=result.url,
                        title=title,
                        content=result.markdown,
                        source_urls=["https://daa.uit.edu.vn/", url, result.url]
                    )

                    # Only download files if content was actually saved (not skipped)
                    downloaded_files_count = 0
                    if folder_saved:  # folder_saved is None if skipped
                        # Tạo thư mục cho URL hiện tại (đã được tạo trong save_crawled_data)
                        page_folder = create_folder_for_url(result.url)

                        # Lọc và download các file
                        downloadable_links = filter_downloadable_links(result.links["internal"])
                        print(f"Found {len(downloadable_links)} downloadable files for {result.url}")

                        for file_url in downloadable_links:
                            # Tạo absolute URL nếu cần
                            if file_url.startswith('/'):
                                file_url = "https://daa.uit.edu.vn" + file_url
                            elif not file_url.startswith('http'):
                                file_url = "https://daa.uit.edu.vn/" + file_url

                            print(f"📥 Downloading: {file_url}")
                            if download_file(file_url, page_folder):
                                downloaded_files_count += 1

                    crawled_announcements.append({
                        'url': result.url,
                        'title': title,
                        'content_length': len(result.markdown),
                        'downloaded_files': downloaded_files_count,
                        'was_updated': folder_saved is not None
                    })

                    status_emoji = "✅" if folder_saved else "⏭️"
                    print(f"{status_emoji} Processed page: {title[:50]}... (Downloaded {downloaded_files_count} files)")
                else:
                    print(f"✗ No content found: {result.url}")
            else:
                print(f"✗ Failed to crawl: {result.url} - {result.error_message}")

    # Print summary
    print(f"\n--- Crawl Summary ---")
    print(f"Total pages saved: {len(crawled_announcements)}")
    print(f"Sample pages:")
    for ann in crawled_announcements[:5]:
        print(f"- {ann['title'][:60]}...")

    return crawled_announcements

async def crawl_course_url(url: str):
    pass


CRAWLER_FUNCTIONS = {
    "daa": crawl_daa_url,
    # "course": crawl_course_urls
}


async def crawl_group(group_name: str, urls: list[str]):
    crawl_func = CRAWLER_FUNCTIONS.get(group_name)
    if not crawl_func:
        print(f"Crawler function for '{group_name}' not found. Skipping")
        return

    for url in urls:
        try:
            await crawl_func(url)
        except Exception as e:
            print(f"Error crawling '{url}': {e}")


async def crawl_all():
    for group_name, urls in URL_GROUPS.items():
        print(f"Start crawling group: {group_name}")
        await crawl_group(group_name, urls)
        print(f"Finished crawling group: {group_name}")
