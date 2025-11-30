"""
Content quality filter for processing pipeline.

Filters out low-quality content before indexing to avoid noise in vector store.
Uses hybrid approach: rule-based + heuristic scoring.
"""

import re
from typing import Tuple, Dict
from src.shared.config.settings import settings


class ContentFilter:
    """
    Filter low-quality content using rule-based + heuristic approach.

    Filtering stages:
    1. Hard rules (empty, errors, navigation pages)
    2. Heuristic scoring (word count, paragraphs, information density)

    Usage:
        >>> filter = ContentFilter()
        >>> is_useful, reason = filter.is_useful(content, metadata_generator)
        >>> if is_useful:
        ...     save_content()
        ... else:
        ...     print(f"Filtered: {reason}")
    """

    # Hard rule thresholds
    MIN_LENGTH = 100  # Minimum character count
    MAX_LINK_RATIO = 0.7  # Maximum ratio of links to words

    # Error/navigation keywords
    ERROR_KEYWORDS = [
        "page not found", "trang không tồn tại", "không có kết quả"
    ]

    NAVIGATION_KEYWORDS = [
        "đăng nhập", "login", "sitemap", "bản đồ trang"
    ]

    # Useful keywords (for scoring)
    USEFUL_KEYWORDS = [
        "quy định", "quyết định", "học phần", "chương trình",
        "sinh viên", "đào tạo", "môn học", "khóa luận",
        "thực tập", "tốt nghiệp", "điểm", "học kỳ"
    ]

    def __init__(self, min_score: float = None):
        """
        Initialize content filter.

        Args:
            min_score: Minimum score threshold (0-100). If None, use settings.
        """
        self.min_score = min_score or settings.processing.MIN_CONTENT_SCORE

    def is_useful(self, content: str, metadata: Dict = None) -> Tuple[bool, str]:
        """
        Check if content is useful for indexing.

        Args:
            content: Markdown content to check
            metadata: Optional metadata_generator dict

        Returns:
            (is_useful: bool, reason: str)

        Example:
            >>> filter = ContentFilter()
            >>> is_useful, reason = filter.is_useful("# Title\\n\\nContent here...")
            >>> print(is_useful, reason)
            True "passed"
        """
        if not content:
            return False, "empty_content"

        content = content.strip()

        # Phase 1: Hard rules
        passed, reason = self._check_hard_rules(content)
        if not passed:
            return False, reason

        # Phase 2: Heuristic scoring
        score = self._calculate_content_score(content)
        if score < self.min_score:
            return False, f"low_score_{score:.1f}"

        return True, "passed"

    def _check_hard_rules(self, content: str) -> Tuple[bool, str]:
        """
        Check hard filtering rules.

        Returns:
            (passed: bool, reason: str)
        """
        # Rule 1: Minimum length
        if len(content) < self.MIN_LENGTH:
            return False, "too_short"

        # Rule 2: Error page detection
        content_lower = content.lower()
        for keyword in self.ERROR_KEYWORDS:
            if keyword in content_lower:
                return False, "error_page"

        # Rule 3: Navigation page detection
        nav_count = sum(1 for kw in self.NAVIGATION_KEYWORDS if kw in content_lower)
        if nav_count >= 3:  # Multiple navigation keywords
            return False, "navigation_page"

        # Rule 4: Link ratio check
        links = len(re.findall(r'\[.*?\]\(.*?\)', content))
        words = len(content.split())
        if words > 0 and links / words > self.MAX_LINK_RATIO:
            return False, "too_many_links"

        # Rule 5: Only headers, no content
        lines = content.split('\n')
        header_lines = sum(1 for line in lines if line.strip().startswith('#'))
        non_empty_lines = sum(1 for line in lines if line.strip())
        if non_empty_lines > 0 and header_lines / non_empty_lines > 0.8:
            return False, "only_headers"

        return True, "passed_hard_rules"

    def _calculate_content_score(self, content: str) -> float:
        """
        Calculate content quality score (0-100).

        Scoring breakdown:
        - Word count (0-30 points)
        - Paragraph count (0-20 points)
        - Information density (0-30 points)
        - Useful keywords (0-20 points)

        Args:
            content: Markdown content

        Returns:
            Score from 0 to 100
        """
        score = 0.0

        # Component 1: Word count (0-30 points)
        words = content.split()
        word_count = len(words)
        # Scale: 0-300 words → 0-30 points
        score += min(word_count / 300, 1.0) * 30

        # Component 2: Paragraph count (0-20 points)
        paragraphs = content.count('\n\n') + 1
        # Scale: 0-10 paragraphs → 0-20 points
        score += min(paragraphs / 10, 1.0) * 20

        # Component 3: Information density (0-30 points)
        # Ratio of meaningful words (>3 chars, not stop words) to total
        meaningful = self._count_meaningful_words(content)
        if word_count > 0:
            density = meaningful / word_count
            score += density * 30

        # Component 4: Useful keywords (0-20 points)
        content_lower = content.lower()
        keyword_matches = sum(1 for kw in self.USEFUL_KEYWORDS if kw in content_lower)
        # Scale: 0-5 keywords → 0-20 points
        score += min(keyword_matches / 5, 1.0) * 20

        return min(score, 100.0)

    def _count_meaningful_words(self, content: str) -> int:
        """
        Count meaningful words (not stop words, length > 3).

        Args:
            content: Text content

        Returns:
            Count of meaningful words
        """
        words = content.split()

        # Vietnamese stop words (common)
        stop_words = {
            "và", "của", "có", "cho", "từ", "được", "này", "đó",
            "các", "những", "với", "theo", "để", "trong", "nếu",
            "the", "a", "an", "is", "are", "was", "were", "be"
        }

        meaningful = 0
        for word in words:
            # Clean word (remove markdown, punctuation)
            clean_word = re.sub(r'[^a-zA-Zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', '',
                                word.lower())

            # Check if meaningful
            if len(clean_word) > 3 and clean_word not in stop_words:
                meaningful += 1

        return meaningful

    def get_stats_summary(self, content: str) -> Dict:
        """
        Get detailed statistics for debugging/analysis.

        Args:
            content: Content to analyze

        Returns:
            Dict with detailed stats
        """
        words = content.split()
        word_count = len(words)
        paragraphs = content.count('\n\n') + 1
        meaningful = self._count_meaningful_words(content)
        score = self._calculate_content_score(content)

        return {
            "length": len(content),
            "word_count": word_count,
            "paragraph_count": paragraphs,
            "meaningful_words": meaningful,
            "information_density": meaningful / word_count if word_count > 0 else 0,
            "score": score,
            "is_useful": score >= self.min_score
        }
