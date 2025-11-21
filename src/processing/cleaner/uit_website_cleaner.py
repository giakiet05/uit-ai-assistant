"""
UIT Website generic content cleaner
"""
from .base_cleaner import BaseCleaner


class UitWebsiteCleaner(BaseCleaner):
    """Cleaner for content from UIT websites, using a pattern-based approach."""

    def __init__(self):
        # Patterns to skip at the beginning (before main content)
        super().__init__()
        self.skip_patterns_start = [
            'Skip to content', 'Skip to navigation', 'Navigation menu',
            'Tìm kiếm', 'Đăng Nhập', 'Liên kết', 'Back to top',
            '--------- Liên kết website -------', 'Website trường',
            'Webmail', 'Website môn học', 'Tài khoản chứng thực',
            'Diễn đàn sinh viên', 'Microsoft Azure', 'Khoa Công Nghệ',
            'Khoa Hệ Thống', 'Khoa Kỹ Thuật', 'Khoa Mạng Máy Tính',
            'Khoa Khoa Học Máy Tính'
        ]

        # Navigation menu indicators
        self.nav_indicators = [
            '* [Home]', '* [Giới thiệu]', '* [Thông báo]',
            '* [Quy định - Hướng dẫn]', '* [Kế hoạch năm]',
            '* [Chương trình đào tạo]', '* [Lịch]'
        ]

        # End patterns (where we stop collecting content)
        self.end_patterns = [
            'Bài viết liên quan',  # Stop immediately when we see related articles
            'Trang \d' ,  # Pagination starts here
            'PHÒNG ĐÀO TẠO ĐẠI HỌC',
            'Back to top'
        ]

    def clean(self, content: str) -> str:
        """
        Dọn dẹp content DAA một cách đơn giản và hiệu quả.

        Steps:
        1. Remove letterhead (ĐẠI HỌC QUỐC GIA, CỘNG HÒA XÃ HỘI CHỦ NGHĨA, etc.)
        2. Remove navigation junk (Skip to content, menu, etc.)
        3. Collect main content from first H1 until end patterns
        """
        if not content:
            return ""

        # Step 1: Remove letterhead first
        content = self.remove_letterhead(content)

        # Step 2: Remove navigation junk and collect main content
        lines = content.split('\n')
        cleaned_lines = []
        collecting = False  # Dùng một cái tên rõ ràng hơn

        for line in lines:
            line = line.strip()

            # --- Logic của Người Sưu Tầm Thông Minh ---

            if not collecting:
                # 1. TÌM ĐIỂM BẮT ĐẦU: Chỉ cần thấy '# ' là bắt đầu hốt!
                if line.startswith('# '):
                    collecting = True
                    cleaned_lines.append(line)  # Nhớ hốt luôn cả dòng này nhé!
            else:
                # 2. KIỂM TRA ĐIỂM DỪNG: Thấy rác là dừng lại ngay lập tức
                if any(pattern in line for pattern in self.end_patterns):
                    break  # Dừng vòng lặp, không xử lý thêm nữa

                # 3. HỐT HÀNG: Nếu không phải điểm dừng, cứ bỏ vào giỏ
                if line:  # Chỉ thêm những dòng có nội dung
                    cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def remove_letterhead(self, content: str) -> str:
        """
        Remove common document letterheads from regulation documents.

        Letterheads are the formal headers at the beginning of official documents:
        - ĐẠI HỌC QUỐC GIA TP.HCM
        - TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN
        - CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
        - Độc lập - Tự do - Hạnh phúc
        - Số: XXX/QĐ-ĐHCNTT
        - Tp. Hồ Chí Minh, ngày...

        These are metadata-like headers that don't contribute to semantic search.
        Real content starts with headers like "QUYẾT ĐỊNH", "THÔNG BÁO", "CÔNG VĂN", etc.

        If no letterhead is detected, returns original content unchanged.

        Args:
            content: Markdown content with letterhead

        Returns:
            Content with letterhead removed, or original if no letterhead found
        """
        import re

        if not content:
            return ""

        lines = content.split('\n')

        # Letterhead patterns (order matters!)
        letterhead_patterns = [
            r'^#\s*ĐẠI HỌC QUỐC GIA',
            r'^##\s*TRƯỜNG ĐẠI HỌC',
            r'^#\s*CỘNG HÒA XÃ HỘI CHỦ NGHĨA',
            r'^##\s*Độc lập\s*-\s*Tự do\s*-\s*Hạnh phúc',
            r'^Số:\s*\d+',
            r'^Tp\.\s*Hồ Chí Minh,\s*ngày',
            r'^----+\s*$',  # Horizontal rules separating letterhead from content
        ]

        # Content start markers (real content begins with these)
        content_start_markers = [
            r'^#\s*(QUYẾT ĐỊNH|THÔNG BÁO|CÔNG VĂN|THÔNG TIN|QUY ĐỊNH|QUY CHẾ)',
        ]

        # First pass: check if this document has letterhead at all
        has_letterhead = False
        for line in lines[:10]:  # Only check first 10 lines
            stripped = line.strip()
            if any(re.match(pattern, stripped, re.IGNORECASE) for pattern in letterhead_patterns):
                has_letterhead = True
                break

        # If no letterhead detected, return original content
        if not has_letterhead:
            return content

        # Second pass: remove letterhead
        cleaned_lines = []
        found_content_start = False

        for line in lines:
            stripped = line.strip()

            # Check if we've reached real content
            if not found_content_start:
                is_content_start = any(
                    re.match(pattern, stripped, re.IGNORECASE)
                    for pattern in content_start_markers
                )

                if is_content_start:
                    found_content_start = True
                    cleaned_lines.append(line)
                    continue

                # Check if this line is letterhead
                is_letterhead = any(
                    re.match(pattern, stripped, re.IGNORECASE)
                    for pattern in letterhead_patterns
                )

                # Skip letterhead lines and empty lines before content starts
                if is_letterhead or not stripped:
                    continue

            # Once we've found content start, keep everything
            if found_content_start:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    # def extract_title(self, content: str) -> str:
    #     """Extract the main title from DAA content"""
    #     lines = content.split('\n')
    #     for line in lines:
    #         if line.startswith('# '):
    #             return line[2:].strip()
    #     return ""  # Return empty string instead of None
