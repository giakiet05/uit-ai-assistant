"""
Factory for creating appropriate cleaners based on category
"""
from typing import Type, Dict
from .base_cleaner import BaseCleaner
from .uit_website_cleaner import UitWebsiteCleaner


class PassthroughCleaner(BaseCleaner):
    """A cleaner that does nothing, just passes the content through."""
    def clean(self, content: str) -> str:
        return content


class CleanerFactory:
    """Factory to create appropriate cleaner for different content categories"""

    # This dictionary maps a category string to a cleaner CLASS.
    _cleaners: Dict[str, Type[BaseCleaner]] = {
        'curriculum': UitWebsiteCleaner,
        'regulation': UitWebsiteCleaner,
        # Future categories can be added here
    }

    @classmethod
    def get_cleaner(cls, category: str) -> BaseCleaner:
        """
        Get an INSTANCE of the appropriate cleaner based on a category name.

        Args:
            category: The category name (e.g., 'curriculum', 'regulation').

        Returns:
            An instance of a cleaner. Defaults to PassthroughCleaner if no specific
            cleaner is found.
        """
        # Get the specific cleaner class for the category
        cleaner_class = cls._cleaners.get(category)

        if cleaner_class:
            # If a specific cleaner is found, return an instance of it
            return cleaner_class()
        else:
            # Otherwise, return a default cleaner that does nothing
            return PassthroughCleaner()

    @classmethod
    def register_cleaner(cls, category: str, cleaner_class: Type[BaseCleaner]):
        """
        Register a new cleaner CLASS for a category.

        Args:
            category: The category name to associate with the cleaner.
            cleaner_class: The cleaner class to register.
        """
        if not issubclass(cleaner_class, BaseCleaner):
            raise TypeError("cleaner_class must be a subclass of BaseCleaner")
        cls._cleaners[category] = cleaner_class