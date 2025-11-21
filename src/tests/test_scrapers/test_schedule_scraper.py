"""
Unit tests for schedule scraper.
"""
import pytest
from src.scraper.daa import DaaScheduleScraper
from src.models import Schedule


def test_scraper_with_empty_html():
    """Test scraper handles empty HTML."""
    result = DaaScheduleScraper.scrape("")
    assert "error" in result
    assert result["classes"] == []


def test_scraper_with_invalid_html():
    """Test scraper handles invalid HTML."""
    html = "<html><body>No table here</body></html>"
    result = DaaScheduleScraper.scrape(html)
    assert result["classes"] == []


def test_scraper_with_sample_html(sample_schedule_html):
    """Test scraper with real HTML sample."""
    if sample_schedule_html is None:
        pytest.skip("No sample HTML available")
    
    result = DaaScheduleScraper.scrape(sample_schedule_html)
    
    assert "classes" in result
    assert isinstance(result["classes"], list)
    
    if result["classes"]:
        # Test first class has required fields
        first_class = result["classes"][0]
        assert "subject" in first_class
        assert "period" in first_class


def test_schedule_model_validation():
    """Test Schedule model validation."""
    schedule_data = {
        "student_id": "23520815",
        "semester": "HK1",
        "classes": [
            {
                "day_of_week": "2",
                "period": "1-3",
                "subject": "Trí tuệ nhân tạo",
                "room": "A1.504"
            }
        ]
    }
    
    schedule = Schedule(**schedule_data)
    
    assert schedule.student_id == "23520815"
    assert schedule.total_classes == 1
    assert len(schedule.get_classes_by_day("2")) == 1


def test_schedule_invalid_day():
    """Test Schedule rejects invalid day."""
    from pydantic import ValidationError
    
    # Test 1: Valid days should work
    valid_schedule = Schedule(
        student_id="123",
        classes=[
            {
                "day_of_week": "2",
                "period": "1-3",
                "subject": "Test"
            }
        ]
    )
    assert valid_schedule.classes[0].day_of_week == "2"
    
    # Test 2: Actually invalid day (not in conversion map)
    with pytest.raises(ValidationError):
        Schedule(
            student_id="123",
            classes=[
                {
                    "day_of_week": "99",  # Clearly invalid
                    "period": "1-3",
                    "subject": "Test"
                }
            ]
        )