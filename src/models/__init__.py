"""
Data models for scraped data.
"""
from .schedule import Schedule, ScheduleClass
from .grade import Grades, Course, StudentInfo, GradeSummary
from .exam import ExamSchedule, Exam

__all__ = [
    'Schedule',
    'ScheduleClass',
    'Grades',
    'Course',
    'StudentInfo',
    'GradeSummary',
    'ExamSchedule',
    'Exam',
]