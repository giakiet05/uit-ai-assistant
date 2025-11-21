"""
Grade data models.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from .base import BaseScrapedData


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
    final_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm cuối kỳ")
    average_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm trung bình")
    letter_grade: Optional[str] = Field(None, description="Điểm chữ (A, B+, ...)")
    
    @field_validator('average_score')  # ← Changed
    @classmethod
    def validate_average(cls, v: Optional[float]) -> Optional[float]:
        """Validate average score is within range."""
        if v is not None and (v < 0 or v > 10):
            raise ValueError(f'Average score must be 0-10, got {v}')
        return v


class StudentInfo(BaseModel):
    """Student information."""
    
    model_config = ConfigDict(
        populate_by_name=True  # ← Changed from allow_population_by_field_name
    )
    
    name: Optional[str] = None
    student_id: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    class_name: Optional[str] = Field(None, alias="class")


class GradeSummary(BaseModel):
    """GPA and credit summary."""
    
    total_credits: int = Field(0, description="Tổng số tín chỉ đăng ký")
    completed_credits: int = Field(0, description="Số tín chỉ đã hoàn thành")
    gpa_10: Optional[float] = Field(None, description="GPA hệ 10")
    gpa_4: Optional[float] = Field(None, description="GPA hệ 4")
    
    @classmethod
    def calculate(cls, courses: List[Course]) -> 'GradeSummary':
        """Calculate GPA from courses."""
        total_points = 0
        total_credits = 0
        total_registered = 0
        
        for course in courses:
            total_registered += course.credits
            
            if course.average_score is not None and course.credits > 0:
                total_points += course.average_score * course.credits
                total_credits += course.credits
        
        gpa_10 = round(total_points / total_credits, 2) if total_credits > 0 else None
        gpa_4 = round((gpa_10 / 10) * 4, 2) if gpa_10 else None
        
        return cls(
            total_credits=total_registered,
            completed_credits=total_credits,
            gpa_10=gpa_10,
            gpa_4=gpa_4
        )


class Grades(BaseScrapedData):
    """Complete grades for a student."""
    
    student_info: StudentInfo = Field(default_factory=StudentInfo)
    courses: List[Course] = Field(default_factory=list)
    summary: GradeSummary = Field(default_factory=GradeSummary)
    
    @property
    def total_courses(self) -> int:
        """Total number of courses."""
        return len(self.courses)
    
    def get_courses_above_gpa(self, threshold: float) -> List[Course]:
        """Get courses with score above threshold."""
        return [c for c in self.courses 
                if c.average_score and c.average_score >= threshold]