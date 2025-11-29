"""
Utility functions for parsing HTML content from Crawl4AI.
Uses BeautifulSoup for reliable DOM-based parsing.
"""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

from .models import StudentInfo, GradeSummary, Course, Schedule, ExamSchedule

logger = logging.getLogger(__name__)


# ===== HTML PARSING HELPERS =====

def get_soup(html: str, parser: str = 'lxml') -> BeautifulSoup:
    """Create BeautifulSoup object from HTML."""
    return BeautifulSoup(html, parser)


def find_table_by_content(soup: BeautifulSoup, keywords: List[str]) -> Optional[any]:
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


def extract_table_data(table, skip_header: bool = True) -> List[List[str]]:
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


# ===== DATA CLEANING HELPERS =====

def clean_text(text: Optional[str]) -> Optional[str]:
    """Clean text: strip whitespace, replace multiple spaces"""
    if not text:
        return None
    return ' '.join(text.strip().split())


def parse_int(text: str) -> Optional[int]:
    """Parse integer from text, return None if invalid"""
    if not text or text == '-':
        return None
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return None


def parse_float(text: str) -> Optional[float]:
    """Parse float from text, return None if invalid"""
    if not text or text == '-':
        return None
    try:
        return float(text.strip())
    except (ValueError, AttributeError):
        return None


def extract_semester(text: str) -> Optional[str]:
    """
    Extract semester info from text.

    Patterns to match:
    - "HK 1 NĂM 2025 - 2026"
    - "Học kỳ 2 - Năm học 2024-2025"
    - "THỜI KHOÁ BIỂU HỌC KỲ 1 NĂM 2025 - 2026"
    """
    cleaned_text = text.strip()

    # Pattern 1: "(HK|Học kỳ) X - (Năm học) YYYY - YYYY"
    # This pattern tries to be more robust for different spacing and optional "Năm học"
    match = re.search(r'(?:HK|Học\s*kỳ)\s*(\d+)\s*-\s*(?:Năm\s*học\s*|Năm\s*)?(\d{4})\s*-\s*(\d{4})', cleaned_text, re.IGNORECASE)
    if match:
        semester_num = match.group(1)
        year1 = match.group(2)
        year2 = match.group(3)
        return f"HK{semester_num} năm học {year1}-{year2}"
    
    return None
    
    return None


def extract_student_id(text: str) -> Optional[str]:
    """
    Extract student ID (MSSV) from text - 8 digits.

    MSSV format: YYCCLLL (YY=year, CC=class code, LLL=student number)
    Examples: 23520819, 21520001

    Must not match year ranges like "2025-2026" or phone numbers.
    """
    # Look for "MSSV:" or "Mã SV:" followed by 8 digits
    match = re.search(r'(?:MSSV|Mã\s+SV)[:\s]*(\d{8})\b', text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Fallback: find 8-digit number that starts with 1x, 2x (student ID pattern)
    # This avoids matching phone numbers (09x, 03x) or year ranges (2024-2025)
    match = re.search(r'\b([12]\d{7})\b', text)
    return match.group(1) if match else None


# ===== DOMAIN-SPECIFIC PARSERS =====

def parse_schedule_html(html: str) -> Dict:
    """
    Parse DAA schedule from HTML - simpler approach using card extraction.

    Instead of parsing the complex table structure with rowspan,
    we extract all cards and infer day/period from surrounding structure.
    """
    soup = get_soup(html)

    # Find all course cards
    cards = soup.find_all('div', class_='tkb-card')

    if not cards:
        logger.warning("No schedule cards found")
        return {
            "classes": [],
            "semester": extract_semester(soup.get_text()),
            "student_id": None
        }

    classes = []
    seen_codes = set()  # Track to avoid duplicates

    for card in cards:
        # Extract card type
        card_type = None
        for cls in card.get('class', []):
            if cls in ['lt', 'ht1', 'ht2']:
                card_type = cls
                break

        # Get course code and name
        titles = card.find_all('div', class_='title')
        if len(titles) < 2:
            continue

        subject_code = clean_text(titles[0].get_text())
        subject_name = clean_text(titles[1].get_text())

        # Skip if duplicate (practice classes appear in multiple places)
        card_key = f"{subject_code}_{card_type}"
        if card_key in seen_codes:
            continue
        seen_codes.add(card_key)

        # Get date range and check for specific dates
        all_sub_divs = card.find_all('div', class_='sub')
        date_range = None
        specific_schedule_text = None
        
        if all_sub_divs:
            # First sub_div usually contains the date range
            date_range = clean_text(all_sub_divs[0].get_text())
            # Check if there's a second sub_div or if the first one contains specific schedules
            if len(all_sub_divs) > 1:
                specific_schedule_text = clean_text(all_sub_divs[1].get_text())
            elif re.search(r'Tiết\s+\d+(?:,\d+)*\s+ngày\s+\d{4}-\d{2}-\d{2}', date_range):
                # If first sub_div itself contains specific dates, treat it as such
                specific_schedule_text = date_range

        # Check for specific date pattern within the collected schedule text
        has_specific_dates = False
        if specific_schedule_text and re.search(r'Tiết\s+\d+(?:,\d+)*\s+ngày\s+\d{4}-\d{2}-\d{2}', specific_schedule_text):
            has_specific_dates = True
        
        # Heuristic for "Đồ án" courses: always treat as no fixed schedule
        if "Đồ án" in subject_name:
            has_specific_dates = True

        # Extract room and class size
        badges = card.find_all('span', class_='badge')
        room = None
        class_size = None

        for badge in badges:
            text = badge.get_text(strip=True)
            badge_classes = badge.get('class', [])

            if 'room' in badge_classes:
                room = text.replace('P ', '').strip()
            elif 'size' in badge_classes:
                match = re.search(r'\d+', text)
                if match:
                    class_size = match.group(0)

        day_of_week = None
        period = None

        if not has_specific_dates: # Only try to infer day/period from table structure if no specific dates are present
            parent_cell = card.find_parent('td')
            if parent_cell:
                # Get rowspan for period calculation
                rowspan = int(parent_cell.get('rowspan', 1))

                # Find the row this cell belongs to
                parent_row = parent_cell.find_parent('tr')
                if parent_row:
                    # Get period from first cell of row
                    first_cell = parent_row.find(['td', 'th'])
                    if first_cell:
                        period_text = clean_text(first_cell.get_text())
                        period_match = re.search(r'Tiết\s+(\d+)', period_text)
                        if period_match:
                            period_start = int(period_match.group(1))
                            if rowspan > 1:
                                period = f"{period_start}-{period_start + rowspan - 1}"
                            else:
                                period = str(period_start)

                    # Get day by finding column index
                    # This is tricky - for now, use a simpler heuristic
                    # Look at table header to map columns to days
                    table = parent_cell.find_parent('table')
                    if table:
                        header = table.find('thead')
                        if header:
                            th_cells = header.find_all('th')
                            # Find the actual column index of the parent_cell within its row
                            current_row_cells = parent_row.find_all(['td', 'th'])
                            try:
                                # Find the index of parent_cell in the current row's cells
                                # The first column in th_cells is "Thứ / Tiết", so actual day columns start from index 1
                                # +1 because the th_cells list does not include the first column ("Thứ / Tiết") in its count,
                                # but the current_row_cells.index(parent_cell) would count the first column.
                                col_index_in_row = current_row_cells.index(parent_cell)
                                col_index_in_header = col_index_in_row
                                
                                if col_index_in_header < len(th_cells): # Ensure it's a valid day column
                                    day_text = clean_text(th_cells[col_index_in_header].get_text())
                                    day_match = re.search(r'Thứ\s+(\d+|CN)', day_text, re.IGNORECASE)
                                    if day_match:
                                        day_of_week = day_match.group(1)
                            except ValueError:
                                # parent_cell not found in current_row_cells, can happen with complex table structures
                                pass

        class_data = {
            "subject_code": subject_code,
            "subject": subject_name,
            "type": card_type,
            "room": room,
            "date_range": date_range,
            "class_size": class_size,
        }

        # Add day/period if found
        if day_of_week:
            class_data["day_of_week"] = day_of_week
        if period:
            class_data["period"] = period

        # Remove None values
        class_data = {k: v for k, v in class_data.items() if v is not None}

        if class_data.get("subject_code") and class_data.get("subject"):
            classes.append(class_data)

    return {
        "classes": classes,
        "semester": extract_semester(soup.get_text()),
        "student_id": None  # Don't extract - will use username instead
    }


import re
from typing import List, Dict, Optional, Tuple # Thêm Tuple
from bs4 import BeautifulSoup
import logging
import collections # Thêm collections

from .models import StudentInfo, GradeSummary, Course, Schedule, ExamSchedule, SemesterGrades # Thêm SemesterGrades

logger = logging.getLogger(__name__)


# ===== HTML PARSING HELPERS =====
# ... (các hàm helper khác giữ nguyên)

# ===== DOMAIN-SPECIFIC PARSERS =====

# ... (parse_schedule_html giữ nguyên)

def parse_grades_html(html: str) -> Dict:
    """
    Parse DAA grades from HTML.

    Expected table columns (actual from DAA):
    | STT | Mã HP | Tên học phần | Tín chỉ | Điểm QT | Điểm GK | Điểm TH | Điểm CK | Điểm HP | Ghi chú |
    """
    soup = get_soup(html)

    # --- Extract Student Information ---
    student_info_data = {}
    student_info_table = soup.find('table', attrs={'cellpadding': '0', 'cellspacing': '0', 'border': '0', 'bordercolor': 'FFFFFF', 'width': '100%'})
    if student_info_table:
        # Assuming the structure is consistent:
        # Row 1: Họ và tên, Ngày sinh, Giới tính
        # Row 2: Mã SV, Lớp sinh hoạt, Khoa
        # Row 3: Bậc đào tạo, Hệ đào tạo
        rows = student_info_table.find_all('tr')
        if len(rows) >= 1:
            cells = rows[0].find_all('td')
            if len(cells) >= 6:
                student_info_data["name"] = clean_text(cells[1].get_text())
                student_info_data["dob"] = clean_text(cells[3].get_text())
                student_info_data["gender"] = clean_text(cells[5].get_text())
        if len(rows) >= 2:
            cells = rows[1].find_all('td')
            if len(cells) >= 6: # Mã SV, Lớp sinh hoạt, Khoa
                student_info_data["student_id"] = clean_text(cells[1].get_text())
                student_info_data["class_name"] = clean_text(cells[3].get_text())
                student_info_data["faculty"] = clean_text(cells[5].get_text())
        if len(rows) >= 3:
            cells = rows[2].find_all('td')
            if len(cells) >= 4: # Bậc đào tạo, Hệ đào tạo
                student_info_data["degree"] = clean_text(cells[1].get_text())
                student_info_data["training_system"] = clean_text(cells[3].get_text())

    student_info = StudentInfo(**student_info_data)

    # --- Extract Course Grades Table ---
    table = find_table_by_content(soup, ['Mã HP', 'Tên học phần'])

    if not table:
        logger.warning("Grades table not found")
        return {
            "student_info": student_info.model_dump(),
            "semesters": [], # Return empty list for semesters
            "overall_summary": GradeSummary().model_dump()
        }

    rows_data = extract_table_data(table, skip_header=True)

    courses_by_semester: Dict[str, List[Course]] = collections.defaultdict(list)
    all_courses: List[Course] = []
    current_semester_name = None

    # First pass: parse courses and group by semester
    for row in rows_data:
        # Check for semester header row
        if len(row) == 1 and "Học kỳ" in row[0] and "Trung bình học kỳ" not in clean_text(row[0]): # Ensure it's not the semester GPA row
            current_semester_name = extract_semester(clean_text(row[0]))
            logger.debug(f"Extracted semester header: {current_semester_name} from row: {row[0]}")
            continue

        # Check if it's a course row (STT should be a number)
        stt_val = clean_text(row[0]) if len(row) > 0 else ""
        if not stt_val or not stt_val.isdigit(): # If not a valid STT, it's not a course row, could be a summary row or empty
            continue
        
        # Proceed with course parsing
        stt = parse_int(stt_val)
        if stt is None:
            continue
        
        # Check for "Miễn" score
        is_exempt = False
        average_score_text = clean_text(row[8]) if len(row) > 8 else None
        if average_score_text and "miễn" in average_score_text.lower():
            is_exempt = True
            
        course_data = {
            "stt": stt,
            "course_code": clean_text(row[1]),
            "course_name": clean_text(row[2]),
            "credits": parse_int(row[3]) or 0,
            "attendance_score": None,
            "midterm_score": None,
            "practice_score": None,
            "final_score": None,
            "average_score": None,
            "is_exempt": is_exempt
        }
        
        if not is_exempt:
            course_data["attendance_score"] = parse_float(row[4]) if len(row) > 4 else None
            course_data["midterm_score"] = parse_float(row[5]) if len(row) > 5 else None
            course_data["practice_score"] = parse_float(row[6]) if len(row) > 6 else None
            course_data["final_score"] = parse_float(row[7]) if len(row) > 7 else None
            course_data["average_score"] = parse_float(row[8]) if len(row) > 8 else None

        course_obj = Course(**course_data)
        all_courses.append(course_obj) # Add to overall list
        if current_semester_name:
            courses_by_semester[current_semester_name].append(course_obj)
    
    # Process semesters
    semester_grades_list: List[SemesterGrades] = []
    for sem_name, sem_courses in courses_by_semester.items():
        semester_gpa_10, semester_gpa_4, semester_total_credits = SemesterGrades.calculate_semester_gpa(sem_courses)
        semester_grades_list.append(SemesterGrades(
            semester_name=sem_name,
            courses=sem_courses,
            semester_gpa_10=semester_gpa_10,
            semester_gpa_4=semester_gpa_4,
            semester_total_credits=semester_total_credits
        ))
    
    # Calculate overall summary from all courses
    overall_summary = GradeSummary.calculate(all_courses)

    # Extract overall summary data from HTML (if available) - This part is intentionally omitted
    # as per user request to remove null/redundant fields from GradeSummary.

    return {
        "student_info": student_info.model_dump(),
        "semesters": [s.model_dump() for s in semester_grades_list],
        "overall_summary": overall_summary.model_dump()
    }


def parse_exams_html(html: str) -> Dict:
    """
    Parse DAA exam schedule from HTML.

    Expected table columns:
    | STT | Mã MH | Mã lớp | Ca/Tiết thi | Thứ thi | Ngày thi | Phòng thi | Ghi chú/Hình thức thi |

    Note: This is the ACTUAL structure from DAA, not the simplified version.
    """
    soup = get_soup(html)

    # Extract semester and student_id from page title/header
    semester = extract_semester(soup.get_text())
    student_id = extract_student_id(soup.get_text())
    
    # Try to find exam table - use flexible keywords
    table = find_table_by_content(soup, ['Mã MH', 'thi'])

    if not table:
        logger.warning("Exam table not found")
        return {
            "exams": [],
            "semester": semester,
            "student_id": student_id
        }

    rows_data = extract_table_data(table, skip_header=True)

    exams = []
    for row in rows_data:
        if len(row) < 3: # Minimum data to be a valid exam row
            continue

        # Skip rows without valid STT
        stt_val = clean_text(row[0])
        stt = parse_int(stt_val)
        if stt is None:
            continue
        
        course_code_val = clean_text(row[1]) if len(row) > 1 else None

        # Map columns based on actual DAA structure
        exam = {
            "stt": stt,
            "course_code": course_code_val,
            "course_name": course_code_val, # Use course_code as course_name if no separate name
            "class_code": clean_text(row[2]) if len(row) > 2 else None,
            "exam_period": clean_text(row[3]) if len(row) > 3 else None,
            "day_of_week": clean_text(row[4]) if len(row) > 4 else None,
            "exam_date": clean_text(row[5]) if len(row) > 5 else None,
            "room": clean_text(row[6]) if len(row) > 6 else None,
            "exam_form": clean_text(row[7]) if len(row) > 7 else None,
        }

        # Remove None/empty values (except for course_name which can be course_code)
        # Ensure 'course_name' is not removed if it's derived from course_code
        cleaned_exam = {k: v for k, v in exam.items() if v is not None and v != '' and v != '-'}
        
        # At minimum need course_code or exam_date
        if cleaned_exam.get("course_code") or cleaned_exam.get("exam_date"):
            exams.append(cleaned_exam)

    return {
        "exams": exams,
        "semester": semester,
        "student_id": student_id
    }
