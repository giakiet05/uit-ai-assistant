"""
Test script for hybrid crawler.
Run: python test_hybrid_crawler.py
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from src.knowledge_builder.crawler import DaaStudentCrawler


async def test_full_crawl():
    """Test complete crawl flow."""
    print("\n" + "="*60)
    print("🧪 TESTING HYBRID CRAWLER")
    print("="*60 + "\n")
    
    # Your credentials
    credentials = {
        "username": "23520815",
        "password": "zxc456bnm"
    }
    
    # Create crawler
    crawler = DaaStudentCrawler(
        domain="daa.uit.edu.vn",
        start_url=DaaStudentCrawler.LOGIN_PAGE,
        credentials=credentials
    )
    
    # Run crawl
    result = await crawler.crawl()
    
    # Print results
    print("\n" + "="*60)
    print("📊 RESULTS")
    print("="*60)
    print(f"Success: {result.get('success')}")
    
    if result.get("success"):
        user_data = result.get("user_data", {})
        
        print(f"\n✅ Crawled sections: {user_data.get('crawled_sections')}")
        print(f"❌ Failed sections: {user_data.get('failed_sections')}")
        
        # Schedule
        if "schedule" in user_data.get("crawled_sections", []):
            schedule = user_data["schedule"]["data"]
            print(f"\n📅 Schedule:")
            print(f"  - Classes: {len(schedule.get('classes', []))}")
            print(f"  - Semester: {schedule.get('semester')}")
            if schedule.get('classes'):
                print(f"  - First class: {schedule['classes'][0].get('subject')}")
        
        # Grades
        if "grades" in user_data.get("crawled_sections", []):
            grades = user_data["grades"]["data"]
            print(f"\n📊 Grades:")
            print(f"  - Courses: {len(grades.get('courses', []))}")
            print(f"  - GPA (10): {grades.get('summary', {}).get('gpa_10')}")
            print(f"  - GPA (4): {grades.get('summary', {}).get('gpa_4')}")
            print(f"  - Total credits: {grades.get('summary', {}).get('total_credits')}")
        
        # Check JSON files
        print(f"\n💾 Check output files:")
        print(f"  - data/scraped/{credentials['username']}/schedule.json")
        print(f"  - data/scraped/{credentials['username']}/grades.json")
        print(f"  - data/scraped/{credentials['username']}/exams.json")
    else:
        print(f"\n❌ Error: {result.get('error')}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(test_full_crawl())