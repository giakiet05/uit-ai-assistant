"""
Document metadata generation module.

Generates document-level metadata (7 fields) for each processed file,
combining information from page metadata, filename, and parsed content.
"""
import re
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from urllib.parse import urlparse

from .categorizer import FolderCategorizer


class DocumentMetadataGenerator:
    """
    Generate document-level metadata for processed files.

    Metadata fields:
    1. document_id: Unique ID (folder__filename)
    2. original_url: Source URL (from page metadata)
    3. title: Document title (from content or filename)
    4. category: Content category (from folder pattern)
    5. domain: Source domain (from URL)
    6. published_date: Publication date (cascading fallback, nullable)
    7. crawled_at: Crawl timestamp (from page metadata)
    """

    def __init__(self):
        """Initialize with categorizer."""
        self.categorizer = FolderCategorizer()

    def generate(
        self,
        file_path: Path,
        folder_name: str,
        page_metadata: Dict,
        parsed_content: str
    ) -> Dict:
        """
        Generate complete metadata for a document.

        Args:
            file_path: Path to the document file
            folder_name: Name of parent folder (for document_id)
            page_metadata: Page-level metadata from raw/folder/metadata.json
            parsed_content: Parsed markdown content

        Returns:
            Dict with 7 metadata fields

        Example:
            >>> generator = DocumentMetadataGenerator()
            >>> metadata = generator.generate(
            ...     file_path=Path("1393-qd-dhcntt_29-12-2023.pdf"),
            ...     folder_name="01-quyet-dinh-ve-viec-ban-hanh...",
            ...     page_metadata={"original_url": "https://...", "crawled_at": "..."},
            ...     parsed_content="# QUYẾT ĐỊNH\\n..."
            ... )
            >>> metadata["document_id"]
            "01-quyet-dinh-ve-viec-ban-hanh__1393-qd-dhcntt_29-12-2023"
        """
        filename_stem = file_path.stem  # Without extension

        # 1. document_id: folder__filename (unique identifier)
        document_id = self._generate_document_id(folder_name, filename_stem)

        # 2. original_url: From page metadata
        original_url = page_metadata.get("original_url", "")

        # 3. title: Extract from content, fallback to filename
        title = self._extract_title(parsed_content, filename_stem)

        # 4. category: Infer from folder name
        category = self.categorizer.categorize(folder_name)

        # 5. domain: Extract from URL
        domain = self._extract_domain(original_url)

        # 6. published_date: Cascading extraction (nullable)
        published_date = self._extract_published_date(filename_stem, parsed_content)

        # 7. crawled_at: From page metadata
        crawled_at = page_metadata.get("crawled_at", "")

        return {
            "document_id": document_id,
            "original_url": original_url,
            "title": title,
            "category": category,
            "domain": domain,
            "published_date": published_date,
            "crawled_at": crawled_at
        }

    def _generate_document_id(self, folder_name: str, filename_stem: str) -> str:
        """
        Generate unique document ID from folder + filename.

        Format: {folder}__{filename}

        Args:
            folder_name: Folder name
            filename_stem: Filename without extension

        Returns:
            Unique document ID

        Example:
            >>> self._generate_document_id(
            ...     "01-quyet-dinh-ve-viec...",
            ...     "1393-qd-dhcntt-2023"
            ... )
            "01-quyet-dinh-ve-viec__1393-qd-dhcntt-2023"
        """
        # Combine with double underscore separator
        document_id = f"{folder_name}__{filename_stem}"

        # Sanitize: replace invalid chars with hyphen
        document_id = re.sub(r'[^\w\-]', '-', document_id)

        return document_id

    def _extract_title(self, content: str, fallback: str) -> str:
        """
        Extract document title from markdown content.

        Tries to find first H1 or H2 heading. Falls back to humanized filename.

        Args:
            content: Markdown content
            fallback: Fallback filename stem

        Returns:
            Document title
        """
        if not content:
            return self._humanize_filename(fallback)

        # Try to find first H1 or H2
        match = re.search(r'^##?\s+(.+)$', content, re.MULTILINE)

        if match:
            title = match.group(1).strip()
            # Clean up common markdown artifacts
            title = re.sub(r'\[.*?\]\(.*?\)', '', title)  # Remove links
            title = re.sub(r'[#*_`]', '', title)  # Remove markdown syntax
            return title.strip()

        # Fallback to humanized filename
        return self._humanize_filename(fallback)

    def _humanize_filename(self, filename_stem: str) -> str:
        """
        Convert filename stem to human-readable title.

        Args:
            filename_stem: Filename without extension

        Returns:
            Humanized title

        Example:
            >>> self._humanize_filename("1393-qd-dhcntt_29-12-2023_cap_nhat")
            "1393 qd dhcntt 29 12 2023 cap nhat"
        """
        # Replace separators with spaces
        title = re.sub(r'[-_]', ' ', filename_stem)
        # Clean multiple spaces
        title = re.sub(r'\s+', ' ', title)
        return title.strip()

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain (e.g., "daa.uit.edu.vn")
        """
        if not url:
            return ""

        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""

    def _extract_published_date(
        self,
        filename_stem: str,
        content: str
    ) -> Optional[str]:
        """
        Extract publication date using cascading fallback strategy.

        Strategy:
        1. Try filename pattern: *_DD-MM-YYYY_*
        2. Try content pattern: "ngày DD tháng MM năm YYYY"
        3. Return None (acceptable)

        Args:
            filename_stem: Filename without extension
            content: Document content

        Returns:
            Date in YYYY-MM-DD format, or None

        Example:
            >>> self._extract_published_date("1393-qd-dhcntt_29-12-2023_cap_nhat", "")
            "2023-12-29"
            >>> self._extract_published_date("document", "")
            None
        """
        # Strategy 1: Parse from filename
        date = self._parse_date_from_filename(filename_stem)
        if date:
            return date

        # Strategy 2: Parse from content
        date = self._parse_date_from_content(content)
        if date:
            return date

        # Strategy 3: Return None (acceptable)
        return None

    def _parse_date_from_filename(self, filename: str) -> Optional[str]:
        """
        Parse date from filename pattern: *_DD-MM-YYYY_*

        Args:
            filename: Filename to parse

        Returns:
            Date in YYYY-MM-DD format, or None

        Example:
            >>> self._parse_date_from_filename("1393-qd-dhcntt_29-12-2023_cap_nhat")
            "2023-12-29"
        """
        # Pattern: _DD-MM-YYYY_
        match = re.search(r'_(\d{1,2})-(\d{1,2})-(\d{4})_', filename)

        if match:
            day, month, year = match.groups()
            # Return in YYYY-MM-DD format with zero-padding
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        return None

    def _parse_date_from_content(self, content: str) -> Optional[str]:
        """
        Parse Vietnamese date from content.

        Patterns:
        - "ngày DD tháng MM năm YYYY"
        - "DD/MM/YYYY"

        Args:
            content: Document content

        Returns:
            Date in YYYY-MM-DD format, or None

        Example:
            >>> self._parse_date_from_content("... ngày 29 tháng 12 năm 2023 ...")
            "2023-12-29"
        """
        if not content:
            return None

        # Pattern 1: "ngày DD tháng MM năm YYYY"
        match = re.search(
            r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',
            content
        )
        if match:
            day, month, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Pattern 2: "DD/MM/YYYY"
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', content)
        if match:
            day, month, year = match.groups()
            # Only if year looks valid (20xx or 19xx)
            if year.startswith(('19', '20')):
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        return None


# Convenience function
def generate_document_metadata(
    file_path: Path,
    folder_name: str,
    page_metadata: Dict,
    parsed_content: str
) -> Dict:
    """
    Convenience function to generate metadata for a single document.

    Args:
        file_path: Path to document file
        folder_name: Parent folder name
        page_metadata: Page-level metadata dict
        parsed_content: Parsed markdown content

    Returns:
        Metadata dict with 7 fields

    Example:
        >>> from src.processing.metadata_generator import generate_document_metadata
        >>> metadata = generate_document_metadata(
        ...     file_path=Path("file.pdf"),
        ...     folder_name="01-quyet-dinh...",
        ...     page_metadata={...},
        ...     parsed_content="# Title\\n..."
        ... )
    """
    generator = DocumentMetadataGenerator()
    return generator.generate(file_path, folder_name, page_metadata, parsed_content)
