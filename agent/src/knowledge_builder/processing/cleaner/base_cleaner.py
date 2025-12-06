"""
Base cleaner interface for different content sources
"""
from abc import ABC, abstractmethod

# --- Centralized Config Import ---

class BaseCleaner(ABC):
    """Abstract base class for content cleaners"""

    def __init__(self):
        """Initialize cleaner with data directories from global settings."""
        # No need to pass directories, they are globally available via settings
        pass

    @abstractmethod
    def clean(self, content: str) -> str:
        """Clean the raw content and return processed content"""
        pass
