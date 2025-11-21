"""
Unit tests for grade scraper.
"""
import pytest
from src.scraper.daa import DaaGradeScraper
from src.models import Grades, GradeSummary, Course


def test_scraper_with_empty_html():
    """Test scraper handles empty HTML."""
    result = DaaGradeScraper.scrape("")
    assert "error" in result
    assert result["courses"] == []


def test_scraper_with_sample_html(sample_grades_html):
    """Test scraper with real HTML."""
    if sample_grades_html is None:
        pytest.skip("No sample HTML available")
    
    result = DaaGradeScraper.scrape(sample_grades_html)
    
    assert "courses" in result
    assert isinstance(result["courses"], list)
    
    if result["courses"]:
        first_course = result["courses"][0]
        assert "course_name" in first_course
        assert "credits" in first_course


def test_gpa_calculation():
    """Test GPA calculation logic."""
    courses = [
        Course(
            stt=1,
            course_code="CS101",
            course_name="Test 1",
            credits=3,
            average_score=8.0
        ),
        Course(
            stt=2,
            course_code="CS102",
            course_name="Test 2",
            credits=4,
            average_score=9.0
        ),
    ]
    
    summary = GradeSummary.calculate(courses)
    
    # (3*8.0 + 4*9.0) / 7 = 60/7 = 8.57
    assert summary.total_credits == 7
    assert summary.completed_credits == 7
    assert summary.gpa_10 == pytest.approx(8.57, rel=0.01)
    assert summary.gpa_4 == pytest.approx(3.43, rel=0.01)


def test_gpa_with_missing_scores():
    """Test GPA calculation ignores courses without scores."""
    courses = [
        Course(
            stt=1,
            course_code="CS101",
            course_name="Test",
            credits=3,
            average_score=8.0
        ),
        Course(
            stt=2,
            course_code="CS102",
            course_name="Test 2",
            credits=4,
            average_score=None  # No score
        ),
    ]
    
    summary = GradeSummary.calculate(courses)
    
    assert summary.total_credits == 7  # Both courses counted
    assert summary.completed_credits == 3  # Only scored course
    assert summary.gpa_10 == 8.0  # Only from first course


def test_course_score_validation():
    """Test Course validates score range."""
    # Valid score
    course = Course(
        stt=1,
        course_code="CS101",
        course_name="Test",
        credits=3,
        average_score=8.5
    )
    assert course.average_score == 8.5
    
    # Invalid score (should raise ValidationError)
    with pytest.raises(Exception):
        Course(
            stt=1,
            course_code="CS101",
            course_name="Test",
            credits=3,
            average_score=15.0  # > 10
        )