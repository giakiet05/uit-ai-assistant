import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Use absolute import instead of relative
from src.knowledge_builder.crawler import DaaStudentCrawler


async def test():
    crawler = DaaStudentCrawler(
        domain="daa.uit.edu.vn",
        start_url="https://daa.uit.edu.vn",
        credentials={
            "username": "23520815",
            "password": "zxc456bnm"
        }
    )
    result = await crawler.crawl()
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(result)


if __name__ == "__main__":
    asyncio.run(test())