import hashlib
import json
import requests
import os  # Dùng để lấy tên file từ URL
from datetime import datetime
from urllib.parse import urlparse

from src.crawler.crawler_config import RAW_DATA_DIR


def get_folder_name_from_url(url: str) -> str:
    """Convert URL to folder name by extracting path after domain and replacing / with -"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return 'root'
    return path.replace('/', '-')

def create_folder_for_url(url: str) -> str:
    """Create folder for URL and return the folder path"""
    folder_name = get_folder_name_from_url(url)
    folder_path = os.path.join(RAW_DATA_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def generate_content_hash(content: str) -> str:
    """Generate SHA256 hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def load_existing_metadata(url: str) -> dict:
    """Load existing metadata for a URL if it exists"""
    try:
        folder_path = create_folder_for_url(url)
        metadata_file = os.path.join(folder_path, 'metadata.json')

        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading metadata for {url}: {e}")

    return {}

def should_skip_crawl(url: str, current_content: str) -> tuple[bool, str]:
    """
    Check if we should skip crawling based on content hash
    Returns: (should_skip, reason)
    """
    existing_metadata = load_existing_metadata(url)

    if not existing_metadata:
        return False, "No existing metadata found"

    existing_hash = existing_metadata.get('content_hash')
    current_hash = generate_content_hash(current_content)

    if existing_hash == current_hash:
        return True, "Content unchanged (same hash)"
    else:
        return False, f"Content changed (hash: {existing_hash[:8]}... -> {current_hash[:8]}...)"

def save_crawled_data(url: str, title: str, content: str, source_urls: list = None, force_save: bool = False):
    """Save crawled data in organized folder structure with duplicate detection"""

    # Check if we should skip based on content hash
    if not force_save:
        should_skip, reason = should_skip_crawl(url, content)
        if should_skip:
            print(f"⏭️  Skipped {url}: {reason}")
            return None
        else:
            print(f"💾 Saving {url}: {reason}")

    # Use the new function to create folder
    folder_path = create_folder_for_url(url)

    # Save content.md
    content_file = os.path.join(folder_path, 'content.md')
    with open(content_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # Create metadata
    metadata = {
        "original_url": url,
        "title": title,
        "crawled_at": datetime.now().isoformat() + "Z",
        "content_hash": generate_content_hash(content),
        "source_urls": source_urls or [url]
    }

    # Save metadata.json
    metadata_file = os.path.join(folder_path, 'metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Data saved to: {folder_path}")
    return folder_path

def extract_title_from_content(content: str) -> str:
    """Extract the main title from cleaned content"""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return None

def filter_downloadable_links(links: list) -> list:
    """Filter internal links to get only downloadable files (pdf, doc, xls, etc.)"""
    downloadable_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
    downloadable_links = []

    for link in links:
        href = link.get('href', '')
        if any(href.lower().endswith(ext) for ext in downloadable_extensions):
            downloadable_links.append(href)

    return downloadable_links




def download_file(url: str, save_folder: str) -> bool:
    try:
        os.makedirs(save_folder, exist_ok=True)

        file_name = url.split('/')[-1]
        save_path = os.path.join(save_folder, file_name)

        print(f"🖨️  Bắt đầu tải: {file_name}")

        # 1. Gửi yêu cầu GET, stream=True để tải file lớn mà không ngốn RAM
        # Thêm verify=False để bỏ qua SSL verification cho UIT domain
        response = requests.get(url, stream=True, timeout=30, verify=False)

        # 2. "Bảo vệ": Kiểm tra xem link có tồn tại không (status 200)
        response.raise_for_status()

        # 3. Mở file và ghi dữ liệu nhị phân ('wb')
        with open(save_path, 'wb') as f:
            # 4. Ghi từng mẩu nhỏ (chunk) để tiết kiệm bộ nhớ
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Tải thành công! File đã được lưu tại: {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Tải file thất bại! Lỗi: {e}")
        return False
