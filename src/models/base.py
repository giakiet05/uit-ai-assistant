"""
Base models for all data types.
Provides common fields and utilities.
"""
from pydantic import BaseModel, Field , ConfigDict
from datetime import datetime
from typing import Optional


class BaseScrapedData(BaseModel):
    """Base model for all scraped data."""
    
    # Pydantic V2 style config
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    scraped_at: datetime = Field(default_factory=datetime.now)
    source_url: Optional[str] = None
    student_id: Optional[str] = None