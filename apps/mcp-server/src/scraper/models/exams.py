"""
Pydantic models for exam schedule data.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

from .base import BaseScrapedData


class Exam(BaseModel):
    """Single exam entry."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stt": 1,
                "course_code": "CS314",
                "course_name": "Trí tuệ nhân tạo",
                "class_code": "CS314.Q11",
                "exam_period": "Ca 1",
                "day_of_week": "Thứ 3",
                "exam_date": "20/12/2024",
                "exam_time": "07:30",
                "room": "A1.504",
                "exam_form": "Thi viết"
            }
        }
    )

    stt: Optional[int] = Field(None, description="Số thứ tự")
    course_code: Optional[str] = Field(None, description="Mã môn học")
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "21520001",
                "semester": "HK1 năm học 2024-2025",
                "exams": []
            }
        }
    )

    semester: Optional[str] = Field(None, description="Học kỳ")
    exams: List[Exam] = Field(default_factory=list, description="Danh sách các kỳ thi")

    @property
    def total_exams(self) -> int:
        """Total number of exams."""
        return len(self.exams)
