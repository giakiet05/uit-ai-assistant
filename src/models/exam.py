"""
Exam schedule models.
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
                "exam_date": "20/12/2024",
                "exam_time": "07:30",
                "room": "A1.504",
                "exam_form": "Thi viết"
            }
        }
    )
    
    stt: Optional[int] = None
    course_code: Optional[str] = None
    course_name: str = Field(..., description="Tên môn thi")
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