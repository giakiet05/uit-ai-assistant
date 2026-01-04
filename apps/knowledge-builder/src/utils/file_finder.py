"""
Helper utilities for finding files in the project.
"""

from pathlib import Path
from typing import Optional
from ..config.settings import settings


def find_raw_file(category: str, document_id: str) -> Optional[Path]:
    """
    Find raw file for a document by searching in data/raw/{category}/.

    Args:
        category: Category name (regulation, curriculum, etc.)
        document_id: Document ID (e.g., '790-qd-dhcntt_28-9-22_quy_che_dao_tao')

    Returns:
        Path to raw file if found, None otherwise

    Examples:
        >>> find_raw_file('regulation', '790-qd-dhcntt_28-9-22_quy_che_dao_tao')
        Path('data/raw/regulation/790-qd-dhcntt_28-9-22_quy_che_dao_tao.pdf')
    """
    raw_dir = settings.paths.RAW_DATA_DIR / category

    if not raw_dir.exists():
        return None

    # Try exact match with common extensions
    for ext in ['.pdf', '.docx', '.doc', '.html', '.txt']:
        candidate = raw_dir / f"{document_id}{ext}"
        if candidate.exists():
            return candidate

    # Try fuzzy match (find file starting with document_id)
    for file_path in raw_dir.iterdir():
        if file_path.is_file() and file_path.stem.startswith(document_id):
            return file_path

    return None
