"""
Scraper for DAA schedule page.
"""
from typing import Dict, List
from bs4 import BeautifulSoup
import logging

from ..base_scraper import BaseScraper
from ..utils import extract_student_id, extract_semester, clean_text

logger = logging.getLogger(__name__)


class DaaScheduleScraper(BaseScraper):
    """Scraper for DAA student schedule."""
    
    @classmethod
    def scrape(cls, html: str) -> Dict:
        """
        Main scrape method.
        
        Args:
            html: Raw HTML from schedule page
            
        Returns:
            Dict with schedule data structure
        """
        if not cls.validate_html(html):
            return {
                "error": "Invalid or empty HTML",
                "student_id": None,
                "semester": None,
                "classes": []
            }
        
        soup = cls.get_soup(html)
        
        schedule = {
            "student_id": cls._extract_student_id(soup),
            "semester": cls._extract_semester(soup),
            "classes": cls._extract_schedule_table(soup),
        }
        
        logger.info(f"Scraped {len(schedule['classes'])} classes")
        return schedule
    
    @staticmethod
    def _extract_student_id(soup: BeautifulSoup) -> str:
        """Extract student ID from page."""
        return extract_student_id(soup.get_text())
    
    @staticmethod
    def _extract_semester(soup: BeautifulSoup) -> str:
        """Extract semester info."""
        return extract_semester(soup.get_text())
    
    @classmethod
    def _extract_schedule_table(cls, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract schedule table data.
        """
        # Find table
        table = cls.find_table_by_content(soup, ['thứ', 'tiết', 'môn'])
        
        if not table:
            table = soup.find('table', class_=['schedule', 'timetable', 'view-content'])
        
        if not table:
            table = soup.find('table', id=['schedule', 'timetable'])
        
        if not table:
            tables = soup.find_all('table')
            if tables:
                logger.warning("Using first table as fallback")
                table = tables[0]
        
        if not table:
            logger.error("No schedule table found")
            return []
        
        # Extract rows - SKIP HEADER
        all_rows = table.find_all('tr')
        
        # Find header row index
        header_idx = 0
        for idx, row in enumerate(all_rows):
            text = row.get_text().lower()
            if 'thứ' in text and 'tiết' in text:
                header_idx = idx
                break
        
        # Get data rows (skip header + separator if exists)
        rows_data = []
        for row in all_rows[header_idx + 1:]:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
            
            row_data = [cell.get_text(strip=True) for cell in cells]
            
            # Skip empty or separator rows
            if not row_data or all(not cell or cell == '-' for cell in row_data):
                continue
            
            # Skip header-like rows (contains "Thứ", "Tiết", etc.)
            row_text = ' '.join(row_data).lower()
            if any(header_word in row_text for header_word in ['thứ / tiết', 'day', 'period', 'subject name']):
                continue
            
            rows_data.append(row_data)
        
        classes = []
        for row_data in rows_data:
            if len(row_data) < 3:
                continue
            
            # Parse row
            class_data = {
                "day_of_week": clean_text(row_data[0]) if len(row_data) > 0 else None,
                "period": clean_text(row_data[1]) if len(row_data) > 1 else None,
                "subject": clean_text(row_data[2]) if len(row_data) > 2 else None,
                "subject_code": clean_text(row_data[3]) if len(row_data) > 3 else None,
                "room": clean_text(row_data[4]) if len(row_data) > 4 else None,
                "instructor": clean_text(row_data[5]) if len(row_data) > 5 else None,
                "weeks": clean_text(row_data[6]) if len(row_data) > 6 else None,
            }
            
            # Validate day_of_week is actually a day (number or "CN")
            day = class_data.get("day_of_week", "")
            if not day or not (day.isdigit() or day.upper() == "CN"):
                continue  # Skip invalid rows
            
            # Clean None values
            class_data = {
                k: v for k, v in class_data.items() 
                if v and v not in ['-', 'None', 'N/A', '']
            }
            
            # Only add if has minimum required fields
            if class_data.get("subject") and class_data.get("period"):
                classes.append(class_data)
        
        return classes