"""
Pydantic models for scraped student data.
All models merged into one file for simplicity.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import List, Optional, Tuple # Thêm Tuple


# ===== BASE MODEL =====

class BaseScrapedData(BaseModel):
    """Base model for all scraped data."""
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    scraped_at: datetime = Field(default_factory=datetime.now)
    source_url: Optional[str] = None
    student_id: Optional[str] = None


# ===== SCHEDULE MODELS =====

class ScheduleClass(BaseModel):
    """Single class in schedule (parsed from table layout)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "day_of_week": "4",
                "period": "1-4",
                "subject_code": "SE113.Q11",
                "subject": "Kiểm chứng phần mềm",
                "type": "lt",
                "room": "C314",
                "date_range": "08/09/25 -> 29/11/25",
                "class_size": "80"
            }
        }
    )

    day_of_week: Optional[str] = Field(None, description="Thứ trong tuần (2-7, CN)")
    period: Optional[str] = Field(None, description="Tiết học (VD: 1-4 hoặc 6-8)")
    subject_code: str = Field(..., description="Mã môn học + lớp (VD: SE113.Q11)")
    subject: str = Field(..., description="Tên môn học")
    type: Optional[str] = Field(None, description="Loại lớp (lt=lý thuyết, ht1/ht2=thực hành)")
    room: Optional[str] = Field(None, description="Phòng học")
    date_range: Optional[str] = Field(None, description="Khoảng thời gian học (VD: 08/09/25 -> 29/11/25)")
    class_size: Optional[str] = Field(None, description="Sĩ số lớp")


class Schedule(BaseScrapedData):
    """Complete schedule for a student."""
    
    semester: Optional[str] = Field(None, description="Học kỳ")
    classes: List[ScheduleClass] = Field(default_factory=list)
    
    @property
    def total_classes(self) -> int:
        """Total number of classes."""
        return len(self.classes)


# ===== GRADE MODELS =====

class Course(BaseModel):
    """Single course with grades."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stt": 1,
                "course_code": "CS314",
                "course_name": "Trí tuệ nhân tạo",
                "credits": 4,
                "attendance_score": 9.0,
                "midterm_score": 8.5,
                "final_score": 8.0,
                "average_score": 8.3,
                "letter_grade": "B+"
            }
        }
    )
    
    stt: int = Field(..., description="STT")
    course_code: str = Field(..., description="Mã môn học")
    course_name: str = Field(..., description="Tên môn học")
    credits: int = Field(..., ge=0, le=10, description="Số tín chỉ")
    attendance_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm chuyên cần")
    midterm_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm giữa kỳ")
    practice_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm thực hành")
    final_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm cuối kỳ")
    average_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm trung bình")
    is_exempt: bool = False


class StudentInfo(BaseModel):
    """Student information."""
    
    model_config = ConfigDict(
        populate_by_name=True
    )
    
    name: Optional[str] = None
    student_id: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    class_name: Optional[str] = None
    faculty: Optional[str] = None
    degree: Optional[str] = None
    training_system: Optional[str] = None


class GradeSummary(BaseModel):
    """GPA and credit summary."""
    
    total_registered_credits: int = Field(0, description="Tổng số tín chỉ đăng ký")
    gpa_credits: int = Field(0, description="Số tín chỉ dùng để tính GPA")
    gpa_10: Optional[float] = Field(None, description="GPA hệ 10")
    gpa_4: Optional[float] = Field(None, description="GPA hệ 4")
    
    @classmethod
    def calculate(cls, courses: List[Course]) -> 'GradeSummary':
        """Calculate GPA from courses. This will be the gpa_10 and gpa_4 fields."""
        total_points = 0
        gpa_credits = 0 # credits used for GPA calculation
        total_registered_credits = 0 # total credits attempted/registered
        
        for course in courses:
            total_registered_credits += course.credits
            
            if course.average_score is not None and course.credits > 0:
                total_points += course.average_score * course.credits
                gpa_credits += course.credits
        
        gpa_10 = round(total_points / gpa_credits, 2) if gpa_credits > 0 else None
        gpa_4 = round((gpa_10 / 10) * 4, 2) if gpa_10 else None
        
        return cls(
            total_registered_credits=total_registered_credits,
            gpa_credits=gpa_credits,
            gpa_10=gpa_10,
            gpa_4=gpa_4
        )


class SemesterGrades(BaseModel):
    """Grades for a specific semester."""
    semester_name: str = Field(..., description="Tên học kỳ (e.g., HK1 năm học 2024-2025)")
    courses: List[Course] = Field(default_factory=list)
    semester_gpa_10: Optional[float] = Field(None, description="GPA hệ 10 của học kỳ")
    semester_gpa_4: Optional[float] = Field(None, description="GPA hệ 4 của học kỳ")
    semester_total_credits: int = Field(0, description="Tổng số tín chỉ đăng ký trong học kỳ")

    @classmethod
    def calculate_semester_gpa(cls, courses: List[Course]) -> Tuple[Optional[float], Optional[float], int]:
        total_points = 0
        gpa_credits = 0
        total_registered_credits = 0

        for course in courses:
            total_registered_credits += course.credits
            if course.average_score is not None and course.credits > 0:
                total_points += course.average_score * course.credits
                gpa_credits += course.credits
        
        gpa_10 = round(total_points / gpa_credits, 2) if gpa_credits > 0 else None
        gpa_4 = round((gpa_10 / 10) * 4, 2) if gpa_10 else None
        
        return gpa_10, gpa_4, total_registered_credits


class Grades(BaseScrapedData):
    """Complete grades for a student."""
    
    student_info: StudentInfo = Field(default_factory=StudentInfo)
    semesters: List[SemesterGrades] = Field(default_factory=list)
    overall_summary: GradeSummary = Field(default_factory=GradeSummary)
    
    @property
    def total_semesters(self) -> int:
        """Total number of semesters."""
        return len(self.semesters)

    @property
    def total_courses(self) -> int:
        """Total number of courses across all semesters."""
        return sum(len(s.courses) for s in self.semesters)


# ===== EXAM MODELS =====

class Exam(BaseModel):
    """Single exam entry."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stt": 1,
                "course_code": "CS314",
                "course_name": "Trí tuệ nhân tạo",
                "exam_date": "20/12/2024",
                "exam_time": "07:30",
                "room": "A1.504",
                "exam_form": "Thi viết"
            }
        }
    )
    
    stt: Optional[int] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = Field(None, description="Tên môn thi (hoặc Mã MH nếu không có)")
    class_code: Optional[str] = Field(None, description="Mã lớp")
    exam_period: Optional[str] = Field(None, description="Ca/Tiết thi")
    day_of_week: Optional[str] = Field(None, description="Thứ thi")
    exam_date: Optional[str] = Field(None, description="Ngày thi")
    exam_time: Optional[str] = Field(None, description="Giờ thi")
    room: Optional[str] = Field(None, description="Phòng thi")
    exam_form: Optional[str] = Field(None, description="Hình thức thi")


class ExamSchedule(BaseScrapedData):
    """Complete exam schedule."""
    
    semester: Optional[str] = None
    exams: List[Exam] = Field(default_factory=list)
    
    @property
    def total_exams(self) -> int:
        return len(self.exams)
