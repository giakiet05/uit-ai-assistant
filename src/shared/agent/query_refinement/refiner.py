"""
Query refinement for expanding acronyms before retrieval.
"""

import re
import yaml
from pathlib import Path
from typing import Optional


class QueryRefiner:
    """
    Expands known acronyms in user queries to improve retrieval.

    Strategy:
    1. Find acronyms (2+ uppercase letters)
    2. If all known → expand (append full form)
    3. If has unknown → return None (signal to ask user)
    4. Keep informal language unchanged (embedding handles it)

    Example:
        "điều kiện TN của UIT"
        → "điều kiện TN Tốt nghiệp của UIT Trường Đại học Công nghệ Thông tin"
    """

    def __init__(self, acronym_file: str = "acronyms.yaml"):
        """
        Initialize with acronym dictionary.

        Args:
            acronym_file: Path to YAML file with acronym mappings
        """
        acronym_path = Path(__file__).parent / acronym_file

        if not acronym_path.exists():
            raise FileNotFoundError(f"Acronym file not found: {acronym_path}")

        with open(acronym_path, 'r', encoding='utf-8') as f:
            self.acronyms = yaml.safe_load(f) or {}

    def refine(self, query: str) -> Optional[str]:
        """
        Expand known acronyms in query (case-insensitive).

        Args:
            query: User's original query

        Returns:
            - Expanded query if all acronyms known
            - None if contains unknown acronyms (caller should ask user)
        """
        # Find all potential acronyms (2+ letters, case-insensitive)
        # Pattern: word boundary + letters (uppercase or lowercase)
        acronym_pattern = r'\b([A-ZĐÂĂÊÔƠƯa-zđâăêôơư]{2,})\b'
        found_words = re.findall(acronym_pattern, query)

        # Filter: only words that are likely acronyms
        found_acronyms = []
        for word in found_words:
            # Check if it's likely an acronym:
            # 1. All uppercase (UIT, CNTT, TKB)
            if word.isupper():
                found_acronyms.append(word)
            # 2. All lowercase 2-5 chars AND exists in dictionary (case-insensitive)
            elif word.islower() and 2 <= len(word) <= 5:
                if word.upper() in self.acronyms:
                    found_acronyms.append(word)

        if not found_acronyms:
            # No acronyms → return original
            return query

        # Check if all acronyms are known (case-insensitive lookup)
        unknown_acronyms = []
        for acr in found_acronyms:
            # Convert to uppercase for lookup in dictionary
            if acr.upper() not in self.acronyms:
                unknown_acronyms.append(acr)

        if unknown_acronyms:
            # Has unknown acronyms → return None (signal to ask user)
            return None

        # All acronyms known → expand them
        expanded_query = query

        # Keep track of already expanded acronyms to avoid duplicates
        expanded_set = set()

        for acronym in found_acronyms:
            acr_upper = acronym.upper()

            if acr_upper in expanded_set:
                continue

            full_form = self.acronyms[acr_upper]

            # Pattern: replace "acronym" with "acronym full_form" (case-insensitive)
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(acronym) + r'\b'
            replacement = f"{acronym} ({full_form})"

            # Replace all occurrences
            expanded_query = re.sub(pattern, replacement, expanded_query, flags=re.IGNORECASE)
            expanded_set.add(acr_upper)

        return expanded_query

    def get_unknown_acronyms(self, query: str) -> list[str]:
        """
        Extract unknown acronyms from query (case-insensitive).

        Useful for generating clarification message to user.

        Args:
            query: User's query

        Returns:
            List of unknown acronyms found in query
        """
        # Same logic as refine() to find acronyms
        acronym_pattern = r'\b([A-ZĐÂĂÊÔƠƯa-zđâăêôơư]{2,})\b'
        found_words = re.findall(acronym_pattern, query)

        # Filter likely acronyms (same logic as refine())
        found_acronyms = []
        for word in found_words:
            if word.isupper():
                found_acronyms.append(word)
            elif word.islower() and 2 <= len(word) <= 5:
                if word.upper() in self.acronyms:
                    found_acronyms.append(word)

        # Return unique unknown acronyms (case-insensitive check)
        unknown = [acr for acr in found_acronyms if acr.upper() not in self.acronyms]
        return list(set(unknown))  # Remove duplicates
