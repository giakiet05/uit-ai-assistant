"""
Helper functions for the crawler module.
"""

import json
import re
from urllib.parse import urlparse

import requests
import os
from datetime import datetime

# --- FIX: Import the centralized settings object ---
from ..config import settings

def should_exclude_node_url(url: str) -> bool:
    """Check if URL should be excluded (node/id format)."""
    return bool(re.search(r'/node/\d+', url))


def get_folder_name_from_url(url: str) -> str:
    """Convert URL to folder name by extracting path after domain and replacing / with -"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return 'root'
    return path.replace('/', '-')


def create_or_get_folder_for_url(url: str, base_dir: str) -> str:
    """
    Create or get a unique folder for a URL within its domain's subdirectory.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if not domain:
        raise ValueError(f"Cannot determine domain from URL: {url}")

    domain_folder = os.path.join(base_dir, domain)
    page_folder_name = get_folder_name_from_url(url)
    full_path = os.path.join(domain_folder, page_folder_name)

    os.makedirs(full_path, exist_ok=True)
    return full_path


def save_crawled_data(url: str, title: str, content: str, source_urls: list = None):
    """
    Saves crawled data into an organized folder structure with essential metadata_generator.
    
    Args:
        url: The URL being saved
        title: Title of the content
        content: Markdown content
        source_urls: Optional list of source URLs (for backwards compatibility)
    """
    print(f"[INFO] Saving data for {url}")

    # --- FIX: Use the path from the settings object ---
    folder_path = create_or_get_folder_for_url(url, str(settings.paths.RAW_DATA_DIR))
    content_file = os.path.join(folder_path, 'content.md')
    with open(content_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # --- FIX: Create the simplified, essential metadata_generator object ---
    metadata = {
        "original_url": url,
        "title": title,
        "crawled_at": datetime.now().isoformat() + "Z",
    }

    metadata_file = os.path.join(folder_path, 'metadata_generator.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Data saved to: {folder_path}")
    return folder_path


def save_user_crawled_data(username: str, data_type: str, url: str, title: str, content: str):
    """
    Save user-specific crawled data (schedule, grades, exams).
    
    Args:
        username: User identifier
        data_type: Type of data (schedule, exams, grades)
        url: Source URL
        title: Content title
        content: Markdown content
    """
    print(f"[INFO] Saving {data_type} data for user {username}")
    
    # Create user-specific folder structure
    user_folder = os.path.join(str(settings.paths.RAW_DATA_DIR), "user_data", username)
    data_folder = os.path.join(user_folder, data_type)
    os.makedirs(data_folder, exist_ok=True)
    
    # Save content
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    content_file = os.path.join(data_folder, f'{data_type}_{timestamp}.md')
    with open(content_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Save metadata_generator
    metadata = {
        "username": username,
        "data_type": data_type,
        "original_url": url,
        "title": title,
        "crawled_at": datetime.now().isoformat() + "Z",
    }
    
    metadata_file = os.path.join(data_folder, f'metadata_{timestamp}.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] User data saved to: {data_folder}")
    return data_folder


def extract_title_from_content(content: str) -> str:
    """Extract the main title from cleaned content"""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return ""


def filter_downloadable_links(links: list) -> list:
    """Filter internal links to get only downloadable files (pdf, doc, xls, etc.)"""
    downloadable_links = []
    for link in links:
        href = link.get('href', '')
        # --- FIX: Use downloadable extensions from the settings object ---
        if any(href.lower().endswith(ext) for ext in settings.crawler.DOWNLOADABLE_EXTENSIONS):
            downloadable_links.append(href)
    return downloadable_links


def download_file(url: str, save_folder: str) -> bool:
    try:
        os.makedirs(save_folder, exist_ok=True)
        file_name = url.split('/')[-1]
        save_path = os.path.join(save_folder, file_name)

        print(f"[INFO] Downloading: {file_name} from {url}")
        # --- FIX: Use request timeout from the settings object ---
        response = requests.get(url, stream=True, timeout=settings.crawler.REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[SUCCESS] Downloaded file to: {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download {url}. Error: {e}")
        return False
