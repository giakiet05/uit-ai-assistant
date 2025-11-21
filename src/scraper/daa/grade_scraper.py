"""
Scraper for DAA grades page.
"""
from typing import Dict, List
from bs4 import BeautifulSoup
import logging

from ..base_scraper import BaseScraper
from ..utils import parse_int, parse_float, clean_text, extract_student_id
import re

logger = logging.getLogger(__name__)


class DaaGradeScraper(BaseScraper):
    """Scraper for DAA student grades."""
    
    @classmethod
    def scrape(cls, html: str) -> Dict:
        """
        Main scrape method for grades.
        
        Args:
            html: Raw HTML from grades page
            
        Returns:
            Dict with grades data structure
        """
        if not cls.validate_html(html):
            return {
                "error": "Invalid or empty HTML",
                "student_info": {},
                "courses": []
            }
        
        soup = cls.get_soup(html)
        
        grades = {
            "student_info": cls._extract_student_info(soup),
            "courses": cls._extract_grades_table(soup),
        }
        
        logger.info(f"Scraped {len(grades['courses'])} courses")
        return grades
    
    @staticmethod
    def _extract_student_info(soup: BeautifulSoup) -> Dict:
        """
        Extract student information from page header.
        
        Looks for patterns like:
        - Họ và tên: Nguyễn Văn A
        - Mã SV: 23520815
        - Ngày sinh: 19-12-2005
        """
        info = {}
        text = soup.get_text()
        
        patterns = {
            "name": r'Họ và tên[:\s]*\*?\*?([^\n\|*]+?)\*?\*?(?=\s*\||Ngày sinh|\n)',
            "student_id": r'Mã SV[:\s]*\*?\*?(\d+)',
            "dob": r'Ngày sinh[:\s]*\*?\*?([0-9\-/]+)',
            "gender": r'Giới tính[:\s]*\*?\*?(Nam|Nữ)',
            "class": r'Lớp[^:]*[:\s]*\*?\*?([^\n\|*]+?)\*?\*?(?=\s*\||Ngày sinh|\n)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up markdown artifacts
                value = value.replace('**', '').replace('*', '').strip()
                info[key] = value
        
        return info
    
    @classmethod
    def _extract_grades_table(cls, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract grades table.
        
        Expected columns:
        - STT
        - Mã MH (Course code)
        - Tên môn (Course name)
        - TC (Credits)
        - Điểm CC (Attendance)
        - Điểm GK (Midterm)
        - Điểm CK (Final)
        - Điểm TK (Average)
        - Điểm chữ (Letter grade)
        """
        # Find grades table
        table = cls.find_table_by_content(soup, ['điểm', 'môn'])
        
        if not table:
            table = soup.find('table', class_=['grades', 'view-content'])
        
        if not table:
            tables = soup.find_all('table')
            if tables:
                logger.warning("Using first table for grades")
                table = tables[0]
        
        if not table:
            logger.error("No grades table found")
            return []
        
        # Extract rows
        rows_data = cls.extract_table_data(table, skip_header=True)
        
        courses = []
        for row_data in rows_data:
            if len(row_data) < 4:  # Need at least: STT, code, name, credits
                continue
            
            # Check if it's a valid row (STT should be a number)
            stt = row_data[0].strip()
            if not stt.isdigit():
                continue
            
            course = {
                "stt": parse_int(row_data[0]),
                "course_code": clean_text(row_data[1]) if len(row_data) > 1 else None,
                "course_name": clean_text(row_data[2]) if len(row_data) > 2 else None,
                "credits": parse_int(row_data[3]) if len(row_data) > 3 else 0,
                "attendance_score": parse_float(row_data[4]) if len(row_data) > 4 else None,
                "midterm_score": parse_float(row_data[5]) if len(row_data) > 5 else None,
                "final_score": parse_float(row_data[6]) if len(row_data) > 6 else None,
                "average_score": parse_float(row_data[7]) if len(row_data) > 7 else None,
                "letter_grade": clean_text(row_data[8]) if len(row_data) > 8 else None,
            }
            
            courses.append(course)
        
        return courses