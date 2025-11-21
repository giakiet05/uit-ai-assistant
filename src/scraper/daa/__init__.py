"""
DAA-specific scrapers.
"""
from .schedule_scraper import DaaScheduleScraper
from .grade_scraper import DaaGradeScraper
from .exam_scraper import DaaExamScraper

__all__ = [
    'DaaScheduleScraper',
    'DaaGradeScraper',
    'DaaExamScraper',
]