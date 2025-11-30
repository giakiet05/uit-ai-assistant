"""
Base URL filter class.
"""
from abc import ABC, abstractmethod


class BaseUrlFilter(ABC):
    """Base class for URL filtering."""
    
    @abstractmethod
    def is_important(self, url: str) -> bool:
        """
        Check if URL is important to crawl.
        
        Args:
            url: URL to check
            
        Returns:
            True if should crawl, False otherwise
        """
        pass
    
    @abstractmethod
    def get_priority(self, url: str) -> int:
        """
        Get priority score for URL (0-100).
        Higher = more important.
        
        Args:
            url: URL to score
            
        Returns:
            Priority score (0-100)
        """
        pass