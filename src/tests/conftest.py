"""
Pytest configuration and fixtures.
"""
import pytest
import os


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture
def sample_schedule_html(fixtures_dir):
    """Load sample schedule HTML."""
    filepath = os.path.join(fixtures_dir, 'schedule_sample.html')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None


@pytest.fixture
def sample_grades_html(fixtures_dir):
    """Load sample grades HTML."""
    filepath = os.path.join(fixtures_dir, 'grades_sample.html')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None