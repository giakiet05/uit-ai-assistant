"""
Simple scraper for daa.uit.edu.vn student portal.
Uses BeautifulSoup for reliable HTML parsing.
"""
from typing import Dict

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

from .utils import parse_schedule_html, parse_grades_html, parse_exams_html
from .models import Schedule, Grades, ExamSchedule, GradeSummary, Course


class DaaScraper:
    """
    Scraper for DAA student portal (daa.uit.edu.vn).

    Features:
    - Auto-login with CAPTCHA solving
    - Session management (reuse browser for multiple requests)
    - BeautifulSoup HTML parsing (reliable DOM-based)
    - Pydantic validation

    Usage:
        async with DaaScraper(username, password) as scraper:
            schedule = await scraper.get_schedule()
            grades = await scraper.get_grades()
            exams = await scraper.get_exams()
    """
    
    BASE_URL = "https://daa.uit.edu.vn"
    LOGIN_URL = f"{BASE_URL}/user/login"
    SCHEDULE_URL = f"{BASE_URL}/sinhvien/tkb"
    GRADES_URL = f"{BASE_URL}/sinhvien/kqhoctap"
    EXAMS_URL = f"{BASE_URL}/sinhvien/lichhoc/lichthi"
    
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.crawler = None
        self._is_logged_in = False
    
    async def __aenter__(self):
        """Context manager - init browser and login"""
        config = BrowserConfig(headless=self.headless, verbose=False)
        self.crawler = AsyncWebCrawler(config=config)
        await self.crawler.__aenter__()
        await self._login()
        return self
    
    async def __aexit__(self, *args):
        """Close browser"""
        if self.crawler:
            await self.crawler.__aexit__(*args)
    
    async def _login(self):
        """
        Login to DAA portal with CAPTCHA solving.

        Strategy:
        1. Fill username/password via JavaScript
        2. Extract CAPTCHA answer from label text
        3. Submit form (form submission will trigger navigation)
        4. Verify login success after navigation completes
        """
        # Fill form and submit in ONE go
        # Don't wait for navigation in JS - let Crawl4AI handle it
        js_code = f"""
        (async () => {{
            // Fill credentials
            let nameInput = document.querySelector('#edit-name') || document.querySelector('input[name="name"]');
            if (nameInput) nameInput.value = '{self.username}';

            let passInput = document.querySelector('input[name="pass"]') || document.querySelector('input[type="password"]');
            if (passInput) passInput.value = '{self.password}';

            // Solve CAPTCHA (extract answer from label)
            let captchaLabel = document.querySelector('label[for="edit-english-captcha-answer"]');
            if (captchaLabel) {{
                let questionText = captchaLabel.textContent || captchaLabel.innerText;
                let match = questionText.match(/\\(([^)]+)\\)/);
                if (match && match[1]) {{
                    let answer = match[1].trim();
                    let captchaInput = document.querySelector('#edit-english-captcha-answer');
                    if (captchaInput) {{
                        captchaInput.value = answer;
                        captchaInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                }}
            }}

            // Small delay then submit
            await new Promise(r => setTimeout(r, 500));

            let submitBtn = document.querySelector('#edit-submit') || document.querySelector('input[type="submit"]');
            if (submitBtn) {{
                submitBtn.click();
            }}
            // Don't wait here - let the page navigate naturally
        }})();
        """

        # Execute with wait_for to handle navigation
        result = await self.crawler.arun(
            url=self.LOGIN_URL,
            config=CrawlerRunConfig(
                js_code=js_code,
                session_id="daa_session",
                wait_for="js:() => !window.location.href.includes('/user/login')",
                page_timeout=60000,  # Increased timeout for navigation
                delay_before_return_html=2.0
            )
        )

        # Check if login successful
        if "đăng xuất" in result.html.lower() or "logout" in result.html.lower():
            self._is_logged_in = True
        else:
            raise Exception("DAA login failed - check credentials or CAPTCHA logic")
    
    async def _fetch_html(self, url: str) -> str:
        """Fetch page and return HTML (reuse session)"""
        if not self._is_logged_in:
            raise Exception("Not logged in - use context manager: async with DaaScraper(...)")

        result = await self.crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                session_id="daa_session",
                delay_before_return_html=2.0
            )
        )

        if not result.success:
            raise Exception(f"Failed to fetch {url}: {result.error_message}")

        # Check if session expired (redirected to login)
        if 'edit-name' in result.html.lower() or 'user/login' in result.url.lower():
            raise Exception("Session expired - need to re-login")

        return result.html
    
    async def get_schedule(self) -> dict:
        """
        Get student schedule.

        Returns:
            dict with keys: classes, semester, student_id
        """
        html = await self._fetch_html(self.SCHEDULE_URL)
        data = parse_schedule_html(html)

        # Validate with Pydantic
        schedule = Schedule(
            student_id=data.get("student_id") or self.username,
            semester=data.get("semester"),
            classes=data["classes"]
        )

        return schedule.model_dump()
    
    async def get_grades(self) -> dict:
        """
        Get student grades with GPA calculation.

        Returns:
            dict with keys: student_info, semesters, overall_summary
        """
        html = await self._fetch_html(self.GRADES_URL)
        data = parse_grades_html(html) # data now contains student_info, semesters, overall_summary

        # Validate the entire Grades object with the new structure
        grades = Grades(
            student_id=data.get("student_info", {}).get("student_id") or self.username,
            student_info=data["student_info"],
            semesters=data["semesters"],
            overall_summary=data["overall_summary"]
        )

        return grades.model_dump()
    
    async def get_exams(self) -> dict:
        """
        Get exam schedule.

        Returns:
            dict with keys: exams, semester, student_id
        """
        html = await self._fetch_html(self.EXAMS_URL)
        data = parse_exams_html(html)

        # Validate
        exams = ExamSchedule(
            student_id=data.get("student_id") or self.username,
            semester=data.get("semester"),
            exams=data["exams"]
        )

        return exams.model_dump()
