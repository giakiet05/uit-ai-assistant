"""
Authenticated crawler for DAA student portal (daa.uit.edu.vn).
UPDATED: Now uses custom scrapers for data extraction.
"""
from typing import Dict, Optional
import os
import json
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from .authenticated_crawler import AuthenticatedCrawler
from src.crawler.crawler_helper import save_user_crawled_data

from src.scraper.daa import (
    DaaScheduleScraper,
    DaaGradeScraper,
    DaaExamScraper
)

from src.models import Schedule, Grades, ExamSchedule, GradeSummary

class DaaStudentCrawler(AuthenticatedCrawler):
    """
    Crawler for DAA student portal.
    Login via form on homepage, then access student pages.
    """
    
    
    BASE_URL = "https://daa.uit.edu.vn"
    LOGIN_PAGE = "https://daa.uit.edu.vn/user/login"  
    SCHEDULE_URL = "https://daa.uit.edu.vn/sinhvien/tkb"
    EXAM_URL = "https://daa.uit.edu.vn/sinhvien/lichhoc/lichthi"
    GRADE_URL = "https://daa.uit.edu.vn/sinhvien/kqhoctap"
    
    def __init__(self, domain: str, start_url: str, credentials: Optional[Dict[str, str]] = None):
        super().__init__(domain, start_url, credentials)
        self.headless = False  
    
    async def login(self, crawler: AsyncWebCrawler) -> bool:
        """Login via the form on DAA homepage (left sidebar)."""
        try:
            print(f"\n{'='*60}")
            print(f"🔐 DAA LOGIN - Homepage Login Box")
            print(f"URL: {self.LOGIN_PAGE}")
            print(f"Username: {self.credentials['username']}")
            print(f"{'='*60}\n")
            
            print("[1/2] Loading homepage with login box...")
            
            # JavaScript code (giữ nguyên như cũ)
            js_code = f"""
            (async () => {{
                console.log('Starting DAA login with CAPTCHA extraction...');
                await new Promise(r => setTimeout(r, 2000));
                
                // 1. USERNAME
                let nameInput = document.querySelector('#edit-name') || document.querySelector('input[name="name"]');
                if (nameInput) {{
                    nameInput.value = '{self.credentials["username"]}';
                    console.log('✓ Username filled');
                }}
                
                // 2. PASSWORD
                let passInput = document.querySelector('input[name="pass"]') || document.querySelector('input[type="password"]');
                if (passInput) {{
                    passInput.value = '{self.credentials["password"]}';
                    console.log('✓ Password filled');
                }}
                
                // 3. CAPTCHA
                let captchaLabel = document.querySelector('label[for="edit-english-captcha-answer"]');
                let captchaAnswer = '';
                if (captchaLabel) {{
                    let questionText = captchaLabel.textContent || captchaLabel.innerText;
                    console.log('✓ CAPTCHA question:', questionText);
                    let match = questionText.match(/\(([^)]+)\)/);
                    if (match && match[1]) {{
                        captchaAnswer = match[1].trim();
                        console.log('✓ Extracted answer:', captchaAnswer);
                    }}
                }}
                
                // 4. Fill CAPTCHA
                let captchaInput = document.querySelector('#edit-english-captcha-answer');
                if (captchaInput && captchaAnswer) {{
                    captchaInput.value = captchaAnswer;
                    captchaInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    captchaInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    console.log('✓ CAPTCHA filled');
                }}
                
                await new Promise(r => setTimeout(r, 800));
                
                // 5. SUBMIT
                let submitBtn = document.querySelector('#edit-submit') || document.querySelector('input[type="submit"]');
                if (submitBtn) {{
                    console.log('✓ Submitting...');
                    submitBtn.click();
                    await new Promise(r => setTimeout(r, 3000));
                }}
            }})();
            """
            
            run_config = CrawlerRunConfig(
                js_code=js_code,
                wait_for="css:.user-menu, .logged-in, a[href*='logout'], .tabs.primary",
                delay_before_return_html=5.0,
                page_timeout=30000,
                session_id="daa_student_session",  # ← THÊM ĐÂY - Quan trọng!
            )
            
            print("[2/2] Submitting login form...")
            result = await crawler.arun(url=self.LOGIN_PAGE, config=run_config)
            
            # Check success (giữ nguyên logic cũ)
            if result.success:
                html_lower = result.html.lower()
                success_signs = [
                    'đăng xuất' in html_lower,
                    'logout' in html_lower,
                    'logged-in' in html_lower,
                    'user-menu' in html_lower,
                ]
                failure_signs = [
                    'sai tên đăng nhập' in html_lower,
                    'incorrect username' in html_lower,
                    'sai mật khẩu' in html_lower,
                    'incorrect password' in html_lower,
                ]
                
                if any(success_signs) and not any(failure_signs):
                    print(f"\n[LOGIN] ✅ Login successful!")
                    print(f"[LOGIN] Current URL: {result.url}")
                    return True
                else:
                    print(f"\n[LOGIN] ❌ Login failed")
                    with open('debug_login_failed.html', 'w', encoding='utf-8') as f:
                        f.write(result.html)
                    return False
            
            print(f"[LOGIN] ❌ Request failed: {result.error_message}")
            return False
            
        except Exception as e:
            print(f"[LOGIN] ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False


    async def verify_authentication(self, crawler: AsyncWebCrawler) -> bool:
        """Verify by accessing a student page."""
        try:
            print("\n[AUTH-VERIFY] Checking authentication status...")
            
            result = await crawler.arun(
                url=self.SCHEDULE_URL,
                config=CrawlerRunConfig(
                    wait_for="css:.view-content, .main-content, table, .region-content",
                    delay_before_return_html=2.0,
                    page_timeout=15000,
                    session_id="daa_student_session",  # ← THÊM ĐÂY
                )
            )
            
            if result.success:
                current_url = result.url.lower()
                html_lower = result.html.lower()
                
                if 'sinhvien' in current_url:
                    if any(word in html_lower for word in ['thời khóa biểu', 'lịch học', 'môn học', 'tiết học']):
                        print("[AUTH-VERIFY] ✅ Authentication verified")
                        return True
                
                if current_url == self.BASE_URL.lower() or 'edit-name' in html_lower:
                    print("[AUTH-VERIFY] ❌ Redirected - login required")
                    return False
                
                print("[AUTH-VERIFY] ⚠️ Unclear status")
                return False
            
            print(f"[AUTH-VERIFY] ❌ Request failed")
            return False
            
        except Exception as e:
            print(f"[AUTH-VERIFY] ❌ Exception: {e}")
            return False

    async def crawl_user_data(self, crawler: AsyncWebCrawler) -> Dict:
        """
        Main crawl method - orchestrates everything.
        UPDATED: Now uses custom scrapers + Pydantic models.
        """
        print(f"\n{'='*60}")
        print(f"📚 CRAWLING STUDENT DATA (Hybrid Mode)")
        print(f"User: {self.credentials.get('username')}")
        print(f"{'='*60}\n")
        
        user_data = {
            "username": self.credentials.get("username"),
            "domain": self.domain,
            "crawled_sections": [],
            "failed_sections": [],
        }
        
        # Crawl each section
        sections = [
            ("schedule", self.SCHEDULE_URL, self._crawl_and_parse_schedule),
            ("exams", self.EXAM_URL, self._crawl_and_parse_exams),
            ("grades", self.GRADE_URL, self._crawl_and_parse_grades),
        ]
        
        for i, (key, url, func) in enumerate(sections, 1):
            print(f"\n[{i}/{len(sections)}] 📥 Crawling {key}...")
            result = await func(crawler, url)
            user_data[key] = result
            
            if result.get("success"):
                user_data["crawled_sections"].append(key)
                print(f"  ✅ Success")
            else:
                user_data["failed_sections"].append(key)
                print(f"  ❌ Failed: {result.get('error', 'Unknown')}")
        
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY")
        print(f"✅ Successful: {len(user_data['crawled_sections'])} - {user_data['crawled_sections']}")
        print(f"❌ Failed: {len(user_data['failed_sections'])} - {user_data['failed_sections']}")
        print(f"{'='*60}\n")
        
        return user_data

    async def _crawl_and_parse_schedule(self, crawler: AsyncWebCrawler, url: str) -> Dict:
        """
            Step 1: Fetch HTML (Crawl4AI)
            Step 2: Parse HTML (DaaScheduleScraper)
            Step 3: Validate (Pydantic Schedule model)
            Step 4: Save JSON
        """
        try:
            # Step 1: Fetch HTML
            print("  [1/4] Fetching HTML...")
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    delay_before_return_html=5.0,
                    page_timeout=30000,
                    session_id="daa_student_session",
                )
            )
            
            if not result.success:
                return {"success": False, "error": f"Failed to fetch page: {result.error_message}"}
            
            # Check for redirect to login
            if 'edit-name' in result.html.lower() or 'user/login' in result.url.lower():
                return {"success": False, "error": "Session expired - redirected to login"}
            
            # Save debug HTML
            self._save_debug_html("schedule", result.html)

            # Step 2: Parse with scraper
            print("  [2/4] Parsing HTML...")
            raw_data = DaaScheduleScraper.scrape(result.html)
            
            if "error" in raw_data:
                return {"success": False, "error": raw_data["error"]}
            
            if not raw_data.get("classes"):
                return {
                    "success": False,
                    "error": "No classes found in HTML",
                    "url": result.url,
                    "html_length": len(result.html)
                }
            # Step 3: Validate with Pydantic
            print("  [3/4] Validating data...")
            try:
                schedule = Schedule(
                    student_id=raw_data.get("student_id") or self.credentials["username"],
                    semester=raw_data.get("semester"),
                    classes=raw_data["classes"],
                    source_url=result.url
                )
                # Use model_dump instead of dict
                schedule_dict = schedule.model_dump(mode='json')  # ← Changed
            except Exception as e:
                print(f"  ⚠️ Pydantic validation failed: {e}")
                schedule_dict = raw_data
                schedule_dict["validation_error"] = str(e)
            
            # Step 4: Save JSON
            print("  [4/4] Saving JSON...")
            self._save_json("schedule", schedule_dict)
            
            # Also save markdown (backward compatibility)
            if result.markdown:
                save_user_crawled_data(
                    username=self.credentials["username"],
                    data_type="schedule",
                    url=result.url,
                    title=f"Thời khóa biểu - {self.credentials['username']}",
                    content=result.markdown
                )
            
            return {
                "success": True,
                "url": result.url,
                "data": schedule_dict,
                "classes_count": len(schedule_dict.get("classes", []))
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def _crawl_and_parse_grades(self, crawler: AsyncWebCrawler, url: str) -> Dict:
        """Fetch → Parse → Validate → Calculate GPA → Save"""
        try:
            # Step 1: Fetch
            print("  [1/5] Fetching HTML...")
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    delay_before_return_html=3.0,
                    page_timeout=20000,
                    session_id="daa_student_session",
                )
            )
            
            if not result.success:
                return {"success": False, "error": "Failed to fetch"}
            
            if 'edit-name' in result.html.lower():
                return {"success": False, "error": "Session expired"}
            
            self._save_debug_html("grades", result.html)
            
            # Step 2: Parse
            print("  [2/5] Parsing HTML...")
            raw_data = DaaGradeScraper.scrape(result.html)
            
            if "error" in raw_data:
                return {"success": False, "error": raw_data["error"]}
            
            if not raw_data.get("courses"):
                return {"success": False, "error": "No courses found"}
            
            # Step 3: Calculate GPA
            print("  [3/5] Calculating GPA...")
            from src.models.grade import Course
            courses = [Course(**c) for c in raw_data["courses"]]
            summary = GradeSummary.calculate(courses)
            
            # Step 4: Validate
            print("  [4/5] Validating data...")
            try:
                grades = Grades(
                    student_id=raw_data.get("student_info", {}).get("student_id") or self.credentials["username"],
                    student_info=raw_data["student_info"],
                    courses=courses,
                    summary=summary,
                    source_url=result.url
                )
                grades_dict = grades.model_dump(mode='json')
            except Exception as e:
                print(f"  ⚠️ Pydantic validation failed: {e}")
                grades_dict = raw_data
                grades_dict["summary"] = summary.model_dump(mode="json")
                grades_dict["validation_error"] = str(e)
            
            # Step 5: Save
            print("  [5/5] Saving JSON...")
            self._save_json("grades", grades_dict)
            
            # Backward compatibility
            if result.markdown:
                save_user_crawled_data(
                    username=self.credentials["username"],
                    data_type="grades",
                    url=result.url,
                    title=f"Kết quả học tập - {self.credentials['username']}",
                    content=result.markdown
                )
            
            return {
                "success": True,
                "url": result.url,
                "data": grades_dict,
                "courses_count": len(courses),
                "gpa": summary.gpa_10
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def _crawl_and_parse_exams(self, crawler: AsyncWebCrawler, url: str) -> Dict:
        """Fetch → Parse → Validate → Save"""
        try:
            print("  [1/4] Fetching HTML...")
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    delay_before_return_html=3.0,
                    page_timeout=20000,
                    session_id="daa_student_session",
                )
            )
            
            if not result.success:
                return {"success": False, "error": "Failed to fetch"}
            
            self._save_debug_html("exams", result.html)
            
            print("  [2/4] Parsing HTML...")
            raw_data = DaaExamScraper.scrape(result.html)
            
            if "error" in raw_data:
                return {"success": False, "error": raw_data["error"]}
            
            if not raw_data.get("exams"):
                return {"success": False, "error": "No exams found"}
            
            print("  [3/4] Validating data...")
            try:
                exams = ExamSchedule(
                    student_id=raw_data.get("student_id") or self.credentials["username"],
                    semester=raw_data.get("semester"),
                    exams=raw_data["exams"],
                    source_url=result.url
                )
                exams_dict = exams.model_dump(mode='json')
            except Exception as e:
                print(f"  ⚠️ Validation failed: {e}")
                exams_dict = raw_data
                exams_dict["validation_error"] = str(e)
            
            print("  [4/4] Saving JSON...")
            self._save_json("exams", exams_dict)
            
            if result.markdown:
                save_user_crawled_data(
                    username=self.credentials["username"],
                    data_type="exams",
                    url=result.url,
                    title=f"Lịch thi - {self.credentials['username']}",
                    content=result.markdown
                )
            
            return {
                "success": True,
                "url": result.url,
                "data": exams_dict,
                "exams_count": len(exams_dict.get("exams", []))
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
        
    def _save_debug_html(self, data_type: str, html: str):
        """Save HTML for debugging."""
        debug_dir = f"data/debug/{self.credentials['username']}"
        os.makedirs(debug_dir, exist_ok=True)
        
        filepath = f"{debug_dir}/{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  💾 Debug HTML saved: {filepath}")
    
    def _save_json(self, data_type: str, data: dict):
        """Save structured JSON with datetime handling."""
        import os
        import json
        from datetime import datetime
        
        output_dir = f"data/scraped/{self.credentials['username']}"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = f"{output_dir}/{data_type}.json"
        
        # Custom datetime handler
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=datetime_handler)
        
        print(f"  💾 JSON saved: {filepath}")