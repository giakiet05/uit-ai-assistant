"""
Base Pydantic model for all scraped data.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class BaseScrapedData(BaseModel):
    """Base model for all scraped data."""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

    scraped_at: datetime = Field(default_factory=datetime.now, description="Thời điểm scrape dữ liệu")
    student_id: Optional[str] = Field(None, description="MSSV sinh viên")
