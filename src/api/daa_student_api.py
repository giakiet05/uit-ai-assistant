"""
API endpoints for DAA student portal authenticated crawling.
UPDATED: Returns structured JSON with Pydantic validation.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from src.crawler.daa_student_crawler import DaaStudentCrawler

from src.crawler.daa_student_crawler import DaaStudentCrawler
from src.models import Schedule, Grades, ExamSchedule

router = APIRouter(prefix="/api/daa/student", tags=["daa-student"])


class StudentLoginRequest(BaseModel):
    """Request model for student login credentials."""
    username: str = Field(..., description="Student username/MSSV")
    password: str = Field(..., description="Student password")


class CrawlDataRequest(StudentLoginRequest):
    """Request to crawl specific data types."""
    data_types: List[str] = Field(
        default=["schedule", "exams", "grades"],
        description="Types of data to crawl: schedule, exams, grades"
    )

class ScheduleResponse(BaseModel):
    """Response for schedule data."""
    success: bool
    url: Optional[str]
    data: Optional[Dict[str, Any]]
    classes_count: Optional[int]
    error: Optional[str]


class GradesResponse(BaseModel):
    """Response for grades data."""
    success: bool
    url: Optional[str]
    data: Optional[Dict[str, Any]]
    courses_count: Optional[int]
    gpa: Optional[float]
    error: Optional[str]


class ExamsResponse(BaseModel):
    """Response for exams data."""
    success: bool
    url: Optional[str]
    data: Optional[Dict[str, Any]]
    exams_count: Optional[int]
    error: Optional[str]

class CrawlResponse(BaseModel):
    """Complete crawl response."""
    success: bool
    message: str
    student_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_student_data(request: CrawlDataRequest):
    """
    Crawl student-specific data from DAA portal.
    
    **Required**: Student credentials (username + password)
    
    **Returns**: Thời khóa biểu, Lịch thi, Điểm số
    
    **Security Warning**: 
    - Do NOT store passwords in plain text
    - Use HTTPS only
    - Implement rate limiting
    - Consider using session tokens instead
    """
    try:
        print(f"\n{'='*60}")
        print(f"🎓 DAA STUDENT CRAWL REQUEST (Hybrid Mode)")
        print(f"Username: {request.username}")
        print(f"Data types: {request.data_types}")
        print(f"{'='*60}\n")
        
        # Create crawler with credentials
        crawler = DaaStudentCrawler(
            domain="daa.uit.edu.vn",
            start_url=DaaStudentCrawler.LOGIN_PAGE,
            credentials={
                "username": request.username,
                "password": request.password
            }
        )
        
        # Execute crawl - SỬ DỤNG CÙNG 1 BROWSER SESSION
        result = await crawler.crawl()
        
        if result.get("success"):
            user_data = result.get("user_data", {})
            crawled_sections = user_data.get("crawled_sections", [])
            failed_sections = user_data.get("failed_sections", [])
            
            # Extract summary info
            summary = {
                "crawled_sections": crawled_sections,
                "failed_sections": failed_sections,
                "total_sections": len(crawled_sections) + len(failed_sections),
            }
            
            # Add specific counts
            if "schedule" in crawled_sections:
                schedule_data = user_data.get("schedule", {}).get("data", {})
                summary["classes_count"] = len(schedule_data.get("classes", []))
            
            if "grades" in crawled_sections:
                grades_data = user_data.get("grades", {}).get("data", {})
                summary["courses_count"] = len(grades_data.get("courses", []))
                summary["gpa"] = grades_data.get("summary", {}).get("gpa_10")
            
            if "exams" in crawled_sections:
                exams_data = user_data.get("exams", {}).get("data", {})
                summary["exams_count"] = len(exams_data.get("exams", []))
            
            return CrawlResponse(
                success=True,
                message=f"Successfully crawled {len(crawled_sections)}/{len(crawled_sections) + len(failed_sections)} sections",
                student_id=request.username,
                data=user_data,
                summary=summary
            )
        else:
            error_msg = result.get("error", "Unknown error occurred")
            raise HTTPException(
                status_code=401,
                detail=f"Crawling failed: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API-ERROR] {str(e)}")
        import traceback
        traceback.print_exc()  # ← THÊM: In full stack trace để debug
        raise HTTPException(
            status_code=500,
            detail=f"Server error during crawl: {str(e)}"
        )

@router.post("/schedule", response_model=ScheduleResponse)
async def get_schedule_only(request: StudentLoginRequest):
    """
    Get only schedule data (faster than full crawl).
    
    **Returns**: Structured schedule JSON with class list.
    """
    try:
        crawler = DaaStudentCrawler(
            domain="daa.uit.edu.vn",
            start_url=DaaStudentCrawler.LOGIN_PAGE,
            credentials={
                "username": request.username,
                "password": request.password
            }
        )
        
        result = await crawler.crawl()
        
        if result.get("success"):
            schedule_result = result.get("user_data", {}).get("schedule", {})
            
            if schedule_result.get("success"):
                return ScheduleResponse(
                    success=True,
                    url=schedule_result.get("url"),
                    data=schedule_result.get("data"),
                    classes_count=schedule_result.get("classes_count"),
                    error=None
                )
            else:
                return ScheduleResponse(
                    success=False,
                    url=None,
                    data=None,
                    classes_count=0,
                    error=schedule_result.get("error", "Failed to fetch schedule")
                )
        else:
            raise HTTPException(status_code=401, detail="Login failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grades", response_model=GradesResponse)
async def get_grades_only(request: StudentLoginRequest):
    """
    Get only grades data with calculated GPA.
    
    **Returns**: Structured grades JSON with GPA summary.
    """
    try:
        crawler = DaaStudentCrawler(
            domain="daa.uit.edu.vn",
            start_url=DaaStudentCrawler.LOGIN_PAGE,
            credentials={
                "username": request.username,
                "password": request.password
            }
        )
        
        result = await crawler.crawl()
        
        if result.get("success"):
            grades_result = result.get("user_data", {}).get("grades", {})
            
            if grades_result.get("success"):
                return GradesResponse(
                    success=True,
                    url=grades_result.get("url"),
                    data=grades_result.get("data"),
                    courses_count=grades_result.get("courses_count"),
                    gpa=grades_result.get("gpa"),
                    error=None
                )
            else:
                return GradesResponse(
                    success=False,
                    url=None,
                    data=None,
                    courses_count=0,
                    gpa=None,
                    error=grades_result.get("error", "Failed to fetch grades")
                )
        else:
            raise HTTPException(status_code=401, detail="Login failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-login")
async def test_login(request: StudentLoginRequest):
    """
    Test if student credentials are valid without crawling data.
    Useful for validating login before full crawl.
    """
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig
        
        crawler_instance = DaaStudentCrawler(
            domain="daa.uit.edu.vn",
            start_url=DaaStudentCrawler.LOGIN_PAGE,
            credentials={
                "username": request.username,
                "password": request.password
            }
        )
        
        browser_config = BrowserConfig(verbose=True, headless=False)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            login_success = await crawler_instance.login(crawler)
            
            if login_success:
                auth_verified = await crawler_instance.verify_authentication(crawler)
                
                if auth_verified:
                    return {
                        "success": True,
                        "message": "✅ Login successful and verified",
                        "authenticated": True
                    }
                else:
                    return {
                        "success": False,
                        "message": "⚠️ Login succeeded but verification failed",
                        "authenticated": False
                    }
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials or login failed"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "DAA Student Crawler",
        "version": "2.0.0",
        "mode": "hybrid",
        "features": [
            "Auto CAPTCHA solving",
            "Structured JSON output",
            "Pydantic validation",
            "GPA calculation",
            "Debug HTML saving"
        ]
    }
