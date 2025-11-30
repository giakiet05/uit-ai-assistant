"""
Pydantic models for student schedule data.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

from .base import BaseScrapedData


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

    day_of_week: Optional[str] = Field(None, description="Thứ trong tuần (2-7)")
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
    classes: List[ScheduleClass] = Field(default_factory=list, description="Danh sách các lớp học")

    @property
    def total_classes(self) -> int:
        """Total number of classes."""
        return len(self.classes)
