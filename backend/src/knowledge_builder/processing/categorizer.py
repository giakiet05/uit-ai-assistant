"""
Folder categorization module for processing pipeline.

Categorizes raw folders into content types (regulation, curriculum, announcement, other)
using priority-based pattern matching.
"""
import re
from pathlib import Path
from typing import List, Dict


class FolderCategorizer:
    """
    Categorize folders using priority-based pattern matching.

    Patterns are checked in priority order:
    1. Regulation (highest priority)
    2. Curriculum
    3. Announcement
    4. Other (fallback)

    This ensures that ambiguous folders (e.g., "thongbao-quy-trinh-...")
    are correctly classified as regulation.
    """

    # Category patterns (priority order matters!)
    REGULATION_PATTERNS = [
        r"^\d+-",           # Starts with number: "01-", "27-"
        "quyet-dinh",       # Quyết định
        "quy-dinh",         # Quy định
        "quy-che",          # Quy chế
        "quy-trinh",        # Quy trình
        "huong-dan"         # Hướng dẫn
    ]

    CURRICULUM_PATTERNS = [
        "content-cu-nhan",          # Chương trình cử nhân
        "content-ky-su",            # Chương trình kỹ sư
        "chuong-trinh-dao-tao",     # Chương trình đào tạo
        "danh-muc-mon-hoc",         # Danh mục môn học
        "content-chuong-trinh",     # Content CTĐT
        "chuong-trinh-tien-tien",   # Chương trình tiên tiến
        "de-an-song-nganh",         # Đề án song ngành
        "content-cac-nganh"         # Content các ngành
    ]

    ANNOUNCEMENT_PATTERNS = [
        "thong-bao",            # Thông báo
        "cap-nhat-ket-qua",     # Cập nhật kết quả
        "lich-thi",             # Lịch thi
        "lich-hoc"              # Lịch học
    ]

    CATEGORIES = ["regulation", "curriculum", "announcement", "other"]

    def categorize(self, folder_name: str) -> str:
        """
        Categorize a folder by its name using priority-based pattern matching.

        Args:
            folder_name: Name of the folder (not full path)

        Returns:
            Category: 'regulation', 'curriculum', 'announcement', or 'other'

        Example:
            >>> categorizer = FolderCategorizer()
            >>> categorizer.categorize("01-quyet-dinh-ve-viec...")
            'regulation'
            >>> categorizer.categorize("thongbao-quy-trinh-bao-nghi...")
            'regulation'  # Priority 1 wins over Priority 3
            >>> categorizer.categorize("thong-bao-lich-thi...")
            'announcement'
        """
        folder_lower = folder_name.lower()

        # Priority 1: Regulation (highest)
        for pattern in self.REGULATION_PATTERNS:
            if self._matches_pattern(folder_lower, pattern):
                return "regulation"

        # Priority 2: Curriculum
        for pattern in self.CURRICULUM_PATTERNS:
            if self._matches_pattern(folder_lower, pattern):
                return "curriculum"

        # Priority 3: Announcement
        for pattern in self.ANNOUNCEMENT_PATTERNS:
            if self._matches_pattern(folder_lower, pattern):
                return "announcement"

        # Priority 4: Other (fallback)
        return "other"

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """
        Check if text matches pattern (regex or substring).

        Args:
            text: Text to check (should be lowercase)
            pattern: Pattern to match
                    - If starts with ^: treated as regex
                    - Otherwise: substring match

        Returns:
            True if matches
        """
        if pattern.startswith("^"):
            # Regex pattern
            return bool(re.match(pattern, text))
        else:
            # Substring match
            return pattern in text

    def categorize_batch(self, folder_names: List[str]) -> Dict[str, str]:
        """
        Categorize multiple folders at once.

        Args:
            folder_names: List of folder names

        Returns:
            Dict mapping folder_name -> category
        """
        return {name: self.categorize(name) for name in folder_names}

    def get_folders_by_category(
        self,
        base_path: Path,
        categories: List[str] = None
    ) -> Dict[str, List[Path]]:
        """
        Scan a directory and group folders by category.

        Args:
            base_path: Base directory containing folders
            categories: Filter for specific categories (None = all)

        Returns:
            Dict mapping category -> list of folder paths

        Example:
            >>> categorizer = FolderCategorizer()
            >>> folders = categorizer.get_folders_by_category(
            ...     Path("data/raw/daa.uit.edu.vn"),
            ...     categories=["regulation", "curriculum"]
            ... )
            >>> folders["regulation"]  # List of regulation folder paths
            [Path(...), Path(...), ...]
        """
        # Initialize result dict
        if categories:
            result = {cat: [] for cat in categories}
        else:
            result = {cat: [] for cat in self.CATEGORIES}

        # Scan directory
        if not base_path.exists():
            return result

        for folder in base_path.iterdir():
            if not folder.is_dir():
                continue

            # Categorize
            category = self.categorize(folder.name)

            # Add to result if in filter
            if categories is None or category in categories:
                if category in result:
                    result[category].append(folder)

        return result

    def get_available_categories(self) -> List[str]:
        """Return all possible categories."""
        return self.CATEGORIES.copy()


# Convenience function for simple usage
def categorize_folder(folder_name: str) -> str:
    """
    Convenience function to categorize a single folder.

    Args:
        folder_name: Name of folder

    Returns:
        Category string

    Example:
        'regulation'
    """
    categorizer = FolderCategorizer()
    return categorizer.categorize(folder_name)
