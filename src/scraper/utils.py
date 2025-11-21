"""
Utility functions for scrapers.
"""
import re
from typing import Optional


def parse_int(text: str) -> int:
    """Extract integer from text."""
    try:
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 0
    except:
        return 0


def parse_float(text: str) -> Optional[float]:
    """Extract float from text."""
    try:
        # Replace comma with dot
        cleaned = text.replace(',', '.').strip()
        # Remove any non-numeric except dot
        cleaned = re.sub(r'[^\d.]', '', cleaned)
        return float(cleaned) if cleaned else None
    except:
        return None


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove common markers
    text = text.replace('*', '').replace('|', '').strip()
    return text


def extract_student_id(text: str) -> Optional[str]:
    """Extract student ID from text."""
    patterns = [
        r'(?:MSSV|Mã SV|Student ID)[:\s]*(\d{8})',
        r'\b(\d{8})\b'  # Fallback: any 8-digit number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_semester(text: str) -> Optional[str]:
    """Extract semester info from text."""
    patterns = [
        r'Học kỳ\s*(\d+)',
        r'HK\s*(\d+)',
        r'Semester\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"HK{match.group(1)}"
    
    return None