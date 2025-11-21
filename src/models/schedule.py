"""
Schedule data models.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from .base import BaseScrapedData


class ScheduleClass(BaseModel):
    """Single class in schedule."""
    
    # Pydantic V2 config
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "day_of_week": "2",
                "period": "1-3",
                "subject": "Trí tuệ nhân tạo",
                "subject_code": "CS314",
                "room": "A1.504",
                "instructor": "Nguyễn Văn A"
            }
        }
    )
    
    day_of_week: str = Field(..., description="Thứ trong tuần (2-7, CN)")
    period: str = Field(..., description="Tiết học (VD: 1-3)")
    subject: str = Field(..., description="Tên môn học")
    subject_code: Optional[str] = Field(None, description="Mã môn học")
    room: Optional[str] = Field(None, description="Phòng học")
    instructor: Optional[str] = Field(None, description="Giảng viên")
    weeks: Optional[str] = Field(None, description="Các tuần học")
    
    @field_validator('day_of_week')  # ← Changed from @validator
    @classmethod
    def validate_day(cls, v: str) -> str:
        """Validate day of week."""
        valid_days = ['2', '3', '4', '5', '6', '7', 'CN', 'Sun']
        
        if v in valid_days:
            return v
        
        # Try to convert
        day_map = {
            'Mon': '2', 'Monday': '2',
            'Tue': '3', 'Tuesday': '3',
            'Wed': '4', 'Wednesday': '4',
            'Thu': '5', 'Thursday': '5',
            'Fri': '6', 'Friday': '6',
            'Sat': '7', 'Saturday': '7',
            'Sunday': 'CN', 'CN': 'CN'
        }
        
        converted = day_map.get(v)
        if converted:
            return converted
        
        # If still invalid, raise error
        raise ValueError(f'Invalid day_of_week: {v}. Must be one of {valid_days}')


class Schedule(BaseScrapedData):
    """Complete schedule for a student."""
    
    semester: Optional[str] = Field(None, description="Học kỳ")
    classes: List[ScheduleClass] = Field(default_factory=list)
    
    @property
    def total_classes(self) -> int:
        """Total number of classes."""
        return len(self.classes)
    
    def get_classes_by_day(self, day: str) -> List[ScheduleClass]:
        """Get all classes for a specific day."""
        return [c for c in self.classes if c.day_of_week == day]
    
    def get_monday_classes(self) -> List[ScheduleClass]:
        """Shortcut for Monday classes."""
        return self.get_classes_by_day('2')