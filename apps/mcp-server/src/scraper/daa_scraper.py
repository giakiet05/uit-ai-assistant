"""
Simple scraper for daa.uit.edu.vn student portal.
Uses BeautifulSoup for reliable HTML parsing.
"""

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from playwright.async_api import async_playwright
from src.scraper.models.exams import ExamSchedule
from src.scraper.models.grades import Grades
from src.scraper.models.schedule import Schedule

from .utils import parse_schedule_html, parse_grades_html, parse_exams_html


class DaaScraper:
    """
    Scraper for DAA student portal (daa.uit.edu.vn).

    Features:
    - Cookie-based authentication (recommended) or username/password login
    - Session management (reuse browser for multiple requests)
    - BeautifulSoup HTML parsing (reliable DOM-based)
    - Pydantic validation

    Usage (cookie-based):
        async with DaaScraper(cookie="PHPSESSID=abc; student_id=123") as scraper:
            schedule = await scraper.get_schedule()
            grades = await scraper.get_grades()

    Usage (username/password - legacy):
        async with DaaScraper(username="21520001", password="password") as scraper:
            schedule = await scraper.get_schedule()
    """

    BASE_URL = "https://daa.uit.edu.vn"
    LOGIN_URL = f"{BASE_URL}/user/login"
    SCHEDULE_URL = f"{BASE_URL}/sinhvien/tkb"
    GRADES_URL = f"{BASE_URL}/sinhvien/kqhoctap"
    EXAMS_URL = f"{BASE_URL}/sinhvien/lichhoc/lichthi"

    def __init__(
        self,
        cookie: str | None = None,
        username: str | None = None,
        password: str | None = None,
        headless: bool = True
    ):
        """
        Initialize DaaScraper with either cookie or username/password.

        Args:
            cookie: Cookie string (e.g., "PHPSESSID=abc; student_id=123")
            username: DAA username (MSSV) - required if cookie not provided
            password: DAA password - required if cookie not provided
            headless: Run browser in headless mode
        """
        if not cookie and not (username and password):
            raise ValueError("Either 'cookie' or 'username+password' must be provided")

        self.cookie = cookie
        self.username = username
        self.password = password
        self.headless = headless
        self.crawler = None
        self._is_logged_in = False
        self._use_cookie_auth = cookie is not None

        # For cookie-based auth, use Playwright directly
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
    
    async def __aenter__(self):
        """Context manager - init browser and authenticate"""
        if self._use_cookie_auth:
            # Use Playwright directly for cookie-based auth
            await self._init_playwright()
            await self._inject_cookies()
        else:
            # Use Crawl4AI for username/password login
            config = BrowserConfig(headless=self.headless, verbose=False)
            self.crawler = AsyncWebCrawler(config=config)
            await self.crawler.__aenter__()
            await self._login()

        return self
    
    async def __aexit__(self, *args):
        """Close browser"""
        if self.crawler:
            await self.crawler.__aexit__(*args)

        # Close Playwright resources
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _init_playwright(self):
        """Initialize Playwright browser for cookie-based auth."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()

    async def _inject_cookies(self):
        """
        Inject cookies into Playwright browser session (skip login).

        Cookie format từ extension: "name1=value1; name2=value2"
        """
        if not self.cookie:
            raise ValueError("Cookie string is empty")

        # Parse cookie string into Playwright cookie format
        cookies = []
        for item in self.cookie.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".daa.uit.edu.vn",
                    "path": "/"
                })

        if not cookies:
            raise ValueError("Invalid cookie format. Expected: 'name1=value1; name2=value2'")

        # Add cookies to browser context
        await self._context.add_cookies(cookies)

        # Navigate to verify login
        await self._page.goto(self.BASE_URL)
        await self._page.wait_for_load_state("networkidle")

        # Check if logged in
        content = await self._page.content()
        if "đăng xuất" in content.lower() or "logout" in content.lower():
            self._is_logged_in = True
            print(f"[DaaScraper] ✅ Cookie auth successful - {len(cookies)} cookies injected")
        else:
            raise Exception(
                "Cookie authentication failed. Cookie may be expired or invalid. "
                "Please re-sync cookies via the extension."
            )

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

        if self._use_cookie_auth:
            # Use Playwright for cookie-based auth
            await self._page.goto(url)
            await self._page.wait_for_load_state("networkidle")

            html = await self._page.content()
            current_url = self._page.url

            # Check if session expired
            if 'edit-name' in html.lower() or 'user/login' in current_url.lower():
                raise Exception("Session expired - cookie may be invalid or expired")

            return html
        else:
            # Use Crawl4AI for username/password auth
            result = await self.crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    session_id="daa_session",
                    delay_before_return_html=2.0
                )
            )

            if not result.success:
                raise Exception(f"Failed to fetch {url}: {result.error_message}")

            if 'edit-name' in result.html.lower() or 'user/login' in result.url.lower():
                raise Exception("Session expired - need to re-login")

            return result.html
    
    async def get_schedule(self) -> Schedule:
        """
        Get student schedule.

        Returns:
            Schedule: Pydantic model containing student schedule data
        """
        html = await self._fetch_html(self.SCHEDULE_URL)
        data = parse_schedule_html(html)

        # Validate with Pydantic and return model directly
        schedule = Schedule(
            student_id=data.get("student_id") or self.username,
            semester=data.get("semester"),
            classes=data["classes"]
        )

        return schedule
    
    async def get_grades(self) -> Grades:
        """
        Get student grades with GPA calculation.

        Returns:
            Grades: Pydantic model containing student grades, GPA, and semester breakdown
        """
        html = await self._fetch_html(self.GRADES_URL)
        data = parse_grades_html(html) # data now contains student_info, semesters, overall_summary

        # Validate the entire Grades object with the new structure and return model directly
        grades = Grades(
            student_id=data.get("student_info", {}).get("student_id") or self.username,
            student_info=data["student_info"],
            semesters=data["semesters"],
            overall_summary=data["overall_summary"]
        )

        return grades
    
    async def get_exams(self) -> ExamSchedule:
        """
        Get exam schedule.

        Returns:
            ExamSchedule: Pydantic model containing exam schedule data
        """
        html = await self._fetch_html(self.EXAMS_URL)
        data = parse_exams_html(html)

        # Validate and return model directly
        exams = ExamSchedule(
            student_id=data.get("student_id") or self.username,
            semester=data.get("semester"),
            exams=data["exams"]
        )

        return exams
