"""
Base scraper class with common functionality.
"""
from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for all scrapers."""
    
    @staticmethod
    def validate_html(html: str, min_length: int = 100) -> bool:
        """Validate HTML is not empty or too short."""
        if not html or len(html) < min_length:
            logger.warning(f"HTML too short: {len(html) if html else 0} chars")
            return False
        return True
    
    @staticmethod
    def get_soup(html: str, parser: str = 'lxml') -> BeautifulSoup:
        """Create BeautifulSoup object from HTML."""
        return BeautifulSoup(html, parser)
    
    @staticmethod
    def find_table_by_content(soup: BeautifulSoup, keywords: list) -> Optional[any]:
        """
        Find table containing specific keywords.
        
        Args:
            soup: BeautifulSoup object
            keywords: List of keywords to search for (case-insensitive)
            
        Returns:
            Table element or None
        """
        tables = soup.find_all('table')
        
        for table in tables:
            text = table.get_text().lower()
            if all(keyword.lower() in text for keyword in keywords):
                return table
        
        return None
    
    @staticmethod
    def extract_table_data(table, skip_header: bool = True) -> list:
        """
        Extract data from table rows.
        
        Args:
            table: BeautifulSoup table element
            skip_header: Skip first row (header)
            
        Returns:
            List of rows, each row is a list of cell values
        """
        if not table:
            return []
        
        rows = table.find_all('tr')
        if skip_header and len(rows) > 1:
            rows = rows[1:]
        
        data = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data:  # Skip empty rows
                data.append(row_data)
        
        return data