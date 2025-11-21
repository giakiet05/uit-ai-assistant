"""
Base class for crawlers that require authentication.
"""
from abc import abstractmethod
from typing import Dict, Optional
from .base_crawler import BaseCrawler
from crawl4ai import AsyncWebCrawler, BrowserConfig


class AuthenticatedCrawler(BaseCrawler):
    """Base class for crawlers requiring user authentication."""
    
    def __init__(self, domain: str, start_url: str, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize authenticated crawler.
        
        Args:
            domain: Target domain
            start_url: Starting URL (typically login URL)
            credentials: Dict with 'username' and 'password'
        """
        super().__init__(domain, start_url)
        self.credentials = credentials or {}
        self.is_authenticated = False
    
    @abstractmethod
    async def login(self, crawler: AsyncWebCrawler) -> bool:
        """
        Perform login operation.
        Must be implemented by subclasses.
        
        Args:
            crawler: The AsyncWebCrawler instance
            
        Returns:
            True if login successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def verify_authentication(self, crawler: AsyncWebCrawler) -> bool:
        """
        Verify if authentication is still valid.
        Can be done by accessing a protected page.
        
        Args:
            crawler: The AsyncWebCrawler instance
            
        Returns:
            True if authenticated, False otherwise
        """
        pass
    
    @abstractmethod
    async def crawl_user_data(self, crawler: AsyncWebCrawler) -> Dict:
        """
        Crawl user-specific data after authentication.
        Goes directly to target pages (no dashboard needed).
        
        Args:
            crawler: The AsyncWebCrawler instance
            
        Returns:
            Dict containing user data
        """
        pass
    
    async def crawl(self):
        """
        Main crawl method with authentication flow.
        Flow: Login → Verify → Crawl Data
        """
        print(f"\n{'='*70}")
        print(f"🚀 AUTHENTICATED CRAWL - {self.domain}")
        print(f"{'='*70}")
        
        if not self.credentials.get('username') or not self.credentials.get('password'):
            return {
                "success": False,
                "error": "Missing credentials (username and password required)"
            }
        
        browser_config = BrowserConfig(
            verbose=True,
            headless=getattr(self, 'headless', False),
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Step 1: Login
            print("\n[STEP 1/2] 🔐 Logging in...")
            login_success = await self.login(crawler)
            
            if not login_success:
                print("\n[RESULT] ❌ Login failed - cannot proceed")
                return {"success": False, "error": "Login failed"}
            
            self.is_authenticated = True
            
            # Step 2: Crawl user data (goes directly to pages)
            print("\n[STEP 2/2] 📥 Crawling user data...")
            user_data = await self.crawl_user_data(crawler)
            
            print(f"\n{'='*70}")
            print(f"✅ CRAWL COMPLETED - {self.domain}")
            print(f"{'='*70}\n")
            
            return {
                "success": True,
                "user_data": user_data
            }
