"""
Scraper module - scrape data from websites using Crawl4AI + markdown parsing.
"""
from .daa_scraper import DaaScraper

__all__ = ["DaaScraper", "Grades", "Schedule"]

from .models import Schedule, Grades
