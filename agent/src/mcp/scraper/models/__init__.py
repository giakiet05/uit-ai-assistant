"""
Pydantic models for scraped student data.

This package contains all data models used by the DAA scraper.
All models inherit from BaseScrapedData and include proper validation + documentation.
"""

from .base import BaseScrapedData
from .schedule import Schedule, ScheduleClass
from .grades import Grades, Course, StudentInfo, GradeSummary, SemesterGrades
from .exams import ExamSchedule, Exam

__all__ = [
    # Base
    "BaseScrapedData",
    # Schedule
    "Schedule",
    "ScheduleClass",
    # Grades
    "Grades",
    "Course",
    "StudentInfo",
    "GradeSummary",
    "SemesterGrades",
    # Exams
    "ExamSchedule",
    "Exam",
]
