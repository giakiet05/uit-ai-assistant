"""
Base Pydantic model for all scraped data.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional


class BaseScrapedData(BaseModel):
    """Base model for all scraped data."""

    model_config = ConfigDict(
        # Use timezone-aware datetime for proper ISO format
        # This ensures FastMCP/JSON schema validation passes
    )

    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Thời điểm scrape dữ liệu (UTC timezone)"
    )
    student_id: Optional[str] = Field(None, description="MSSV sinh viên")
