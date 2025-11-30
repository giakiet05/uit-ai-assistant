"""
Pydantic models for student grades data.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Tuple

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
                "practice_score": 10.0,
                "final_score": 8.0,
                "average_score": 8.3,
                "is_exempt": False

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
    is_exempt: bool = Field(False, description="Môn miễn điểm (vd: GDQP)")


class StudentInfo(BaseModel):
    """Student information."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Nguyễn Văn A",
                "student_id": "21520001",
                "dob": "01/01/2003",
                "gender": "Nam",
                "class_name": "KHMT2021",
                "faculty": "Khoa Khoa học Máy tính",
                "degree": "Kỹ sư",
                "training_system": "Chính quy"
            }
        }
    )

    name: Optional[str] = Field(None, description="Họ và tên sinh viên")
    student_id: Optional[str] = Field(None, description="Mã số sinh viên (MSSV)")
    dob: Optional[str] = Field(None, description="Ngày sinh")
    gender: Optional[str] = Field(None, description="Giới tính")
    class_name: Optional[str] = Field(None, description="Lớp")
    faculty: Optional[str] = Field(None, description="Khoa")
    degree: Optional[str] = Field(None, description="Bậc đào tạo")
    training_system: Optional[str] = Field(None, description="Hệ đào tạo")


class GradeSummary(BaseModel):
    """GPA and credit summary."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_registered_credits": 120,
                "gpa_credits": 115,
                "gpa_10": 8.25,
                "gpa_4": 3.30
            }
        }
    )

    total_registered_credits: int = Field(0, description="Tổng số tín chỉ đăng ký")
    gpa_credits: int = Field(0, description="Số tín chỉ dùng để tính GPA (không bao gồm môn miễn điểm)")
    gpa_10: Optional[float] = Field(None, description="GPA hệ 10")
    gpa_4: Optional[float] = Field(None, description="GPA hệ 4")

    @classmethod
    def calculate(cls, courses: List[Course]) -> 'GradeSummary':
        """Calculate GPA from courses. This will be the gpa_10 and gpa_4 fields."""
        total_points = 0
        gpa_credits = 0  # credits used for GPA calculation
        total_registered_credits = 0  # total credits attempted/registered

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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "semester_name": "HK1 năm học 2024-2025",
                "courses": [],
                "semester_gpa_10": 8.5,
                "semester_gpa_4": 3.4,
                "semester_total_credits": 18
            }
        }
    )

    semester_name: str = Field(..., description="Tên học kỳ (e.g., HK1 năm học 2024-2025)")
    courses: List[Course] = Field(default_factory=list, description="Danh sách môn học trong học kỳ")
    semester_gpa_10: Optional[float] = Field(None, description="GPA hệ 10 của học kỳ")
    semester_gpa_4: Optional[float] = Field(None, description="GPA hệ 4 của học kỳ")
    semester_total_credits: int = Field(0, description="Tổng số tín chỉ đăng ký trong học kỳ")

    @classmethod
    def calculate_semester_gpa(cls, courses: List[Course]) -> Tuple[Optional[float], Optional[float], int]:
        """Calculate GPA for a specific semester."""
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_info": {
                    "name": "Nguyễn Văn A",
                    "student_id": "21520001"
                },
                "semesters": [],
                "overall_summary": {
                    "total_registered_credits": 120,
                    "gpa_credits": 115,
                    "gpa_10": 8.25,
                    "gpa_4": 3.30
                }
            }
        }
    )

    student_info: StudentInfo = Field(default_factory=StudentInfo, description="Thông tin sinh viên")
    semesters: List[SemesterGrades] = Field(default_factory=list, description="Điểm các học kỳ")
    overall_summary: GradeSummary = Field(default_factory=GradeSummary, description="Tổng kết GPA tích lũy")

    @property
    def total_semesters(self) -> int:
        """Total number of semesters."""
        return len(self.semesters)

    @property
    def total_courses(self) -> int:
        """Total number of courses across all semesters."""
        return sum(len(s.courses) for s in self.semesters)
