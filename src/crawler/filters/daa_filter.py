"""
URL filter specifically for daa.uit.edu.vn domain.
"""
import re
from .base_filter import BaseUrlFilter


class DaaUrlFilter(BaseUrlFilter):
    """
    Filter URLs cho domain DAA.
    Chỉ crawl những URLs thực sự quan trọng.
    """
    
    # Whitelist: Các patterns QUAN TRỌNG
    IMPORTANT_PATTERNS = [
        r'/thong-bao/',
        r'/quy-dinh/',
        r'/lich-thi/',
        r'/tot-nghiep/',
        r'/hoc-tap/',
        r'/ke-hoach/',
        r'/ban-hanh/',
        r'/huong-dan/',
        r'/bieu-mau/',
        r'/mau-bieu/',
    ]
    
    # Blacklist: Các patterns KHÔNG QUAN TRỌNG
    EXCLUDE_PATTERNS = [
        r'/node/\d+',              # Node URLs
        r'/user/',                 # User pages
        r'/admin/',                # Admin pages
        r'/search/',               # Search results
        r'/comment/',              # Comments
        r'\?page=\d+',            # Pagination
        r'/printpdf/',            # Print PDF
        r'/print/',               # Print
        r'/share/',               # Share links
        r'/taxonomy/',            # Taxonomy
    ]
    
    # Các năm được chấp nhận (thông tin gần đây)
    VALID_YEARS = ['2022', '2023', '2024', '2025']
    
    def is_important(self, url: str) -> bool:
        """
        Kiểm tra URL có quan trọng không.
        
        Logic:
        1. Check blacklist → reject nếu match
        2. Check whitelist → accept nếu match VÀ có năm hợp lệ
        3. Mặc định → reject
        """
        # Step 1: Check blacklist
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # Step 2: Check whitelist
        for pattern in self.IMPORTANT_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                # Nếu có năm trong URL, phải là năm hợp lệ
                if self._has_year(url):
                    return self._has_valid_year(url)
                # Nếu không có năm, chấp nhận
                return True
        
        # Step 3: Default reject
        return False
    
    def get_priority(self, url: str) -> int:
        """
        Tính priority score (0-100).
        Càng cao càng quan trọng.
        """
        score = 0
        
        # Base score theo pattern
        priority_weights = {
            r'/thong-bao/': 50,
            r'/quy-dinh/': 45,
            r'/lich-thi/': 40,
            r'/tot-nghiep/': 40,
            r'/hoc-tap/': 35,
            r'/ke-hoach/': 30,
            r'/huong-dan/': 30,
        }
        
        for pattern, weight in priority_weights.items():
            if re.search(pattern, url, re.IGNORECASE):
                score += weight
                break
        
        # Bonus cho năm gần đây
        if '2025' in url:
            score += 30
        elif '2024' in url:
            score += 20
        elif '2023' in url:
            score += 10
        
        # Penalty cho URL quá dài (có thể là lỗi)
        if len(url) > 150:
            score -= 20
        
        return max(0, min(100, score))
    
    def _has_year(self, url: str) -> bool:
        """Check if URL contains a 4-digit year."""
        return bool(re.search(r'\d{4}', url))
    
    def _has_valid_year(self, url: str) -> bool:
        """Check if URL contains a valid year."""
        for year in self.VALID_YEARS:
            if year in url:
                return True
        return False