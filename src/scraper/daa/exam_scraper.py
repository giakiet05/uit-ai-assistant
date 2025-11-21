"""
Scraper for DAA exam schedule page.
"""
from typing import Dict, List
from bs4 import BeautifulSoup
import logging

from ..base_scraper import BaseScraper
from ..utils import parse_int, clean_text, extract_student_id, extract_semester

logger = logging.getLogger(__name__)


class DaaExamScraper(BaseScraper):
    """Scraper for DAA exam schedule."""
    
    @classmethod
    def scrape(cls, html: str) -> Dict:
        """Main scrape method for exam schedule."""
        if not cls.validate_html(html):
            return {
                "error": "Invalid or empty HTML",
                "student_id": None,
                "semester": None,
                "exams": []
            }
        
        soup = cls.get_soup(html)
        
        exams = {
            "student_id": extract_student_id(soup.get_text()),
            "semester": extract_semester(soup.get_text()),
            "exams": cls._extract_exam_table(soup),
        }
        
        logger.info(f"Scraped {len(exams['exams'])} exams")
        return exams
    
    @classmethod
    def _extract_exam_table(cls, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract exam schedule table.
        
        Expected columns:
        - STT
        - Mã MH (Course code)
        - Tên môn (Course name)
        - Ngày thi (Exam date)
        - Giờ thi (Exam time)
        - Phòng thi (Room)
        - Hình thức (Form)
        """
        table = cls.find_table_by_content(soup, ['thi', 'môn', 'ngày'])
        
        if not table:
            table = soup.find('table', class_=['exam', 'view-content'])
        
        if not table:
            tables = soup.find_all('table')
            if tables:
                table = tables[0]
        
        if not table:
            logger.error("No exam table found")
            return []
        
        rows_data = cls.extract_table_data(table, skip_header=True)
        
        exams = []
        for row_data in rows_data:
            if len(row_data) < 3:
                continue
            
            exam = {
                "stt": parse_int(row_data[0]) if len(row_data) > 0 else None,
                "course_code": clean_text(row_data[1]) if len(row_data) > 1 else None,
                "course_name": clean_text(row_data[2]) if len(row_data) > 2 else None,
                "exam_date": clean_text(row_data[3]) if len(row_data) > 3 else None,
                "exam_time": clean_text(row_data[4]) if len(row_data) > 4 else None,
                "room": clean_text(row_data[5]) if len(row_data) > 5 else None,
                "exam_form": clean_text(row_data[6]) if len(row_data) > 6 else None,
            }
            
            # Clean
            exam = {k: v for k, v in exam.items() if v and v not in ['-', '']}
            
            if exam.get("course_name"):
                exams.append(exam)
        
        return exams