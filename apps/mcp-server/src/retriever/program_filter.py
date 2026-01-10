"""
Program Filter - Extract và filter documents by academic program.

Giải quyết vấn đề nhầm lẫn giữa các ngành tương tự:
- Khoa học Máy tính vs Kỹ thuật Máy tính
- Công nghệ Thông tin vs Hệ thống Thông tin
- Mạng máy tính và Truyền thông dữ liệu vs các ngành khác

Strategy: Hard filtering based on document_id pattern matching
"""

from typing import Optional, List
from llama_index.core.schema import NodeWithScore
from ..utils.logger import logger


# ========== PROGRAM KEYWORDS MAPPING ==========
# Mapping: document_id keyword -> [query keywords to match]

PROGRAM_KEYWORDS = {
    # Khoa học Máy tính
    "khoa-hoc-may-tinh": [
        "khoa học máy tính",
        "khmt",
        "computer science",
        "khoa hoc may tinh",
    ],

    # Kỹ thuật Máy tính
    "ky-thuat-may-tinh": [
        "kỹ thuật máy tính",
        "ktmt",
        "computer engineering",
        "ky thuat may tinh",
        # Note: "kỹ thuật hệ thống máy tính" cũng match pattern này
    ],

    # Công nghệ Thông tin
    "cong-nghe-thong-tin": [
        "công nghệ thông tin",
        "cntt",
        "information technology",
        "cong nghe thong tin",
    ],

    # Hệ thống Thông tin
    "he-thong-thong-tin": [
        "hệ thống thông tin",
        "httt",
        "information systems",
        "he thong thong tin",
    ],

    # Kỹ thuật Phần mềm
    "ky-thuat-phan-mem": [
        "kỹ thuật phần mềm",
        "ktpm",
        "software engineering",
        "ky thuat phan mem",
    ],

    # Khoa học Dữ liệu
    "khoa-hoc-du-lieu": [
        "khoa học dữ liệu",
        "khđl",
        "data science",
        "khoa hoc du lieu",
    ],

    # Trí tuệ Nhân tạo
    "tri-tue-nhan-tao": [
        "trí tuệ nhân tạo",
        "ttnt",
        "artificial intelligence",
        "ai",
        "tri tue nhan tao",
    ],

    # Mạng máy tính và Truyền thông dữ liệu
    "mang-may-tinh-va-truyen-thong-du-lieu": [
        "mạng máy tính và truyền thông dữ liệu",
        "mmtttdl",
        "mạng máy tính",
        "truyền thông dữ liệu",
        "networking",
        "mang may tinh",
    ],

    # An toàn Thông tin
    "an-toan-thong-tin": [
        "an toàn thông tin",
        "attt",
        "information security",
        "cybersecurity",
        "an toan thong tin",
    ],

    # Thương mại điện tử
    "thuong-mai-dien-tu": [
        "thương mại điện tử",
        "tmđt",
        "e-commerce",
        "thuong mai dien tu",
    ],

    # Thiết kế Vi mạch
    "thiet-ke-vi-mach": [
        "thiết kế vi mạch",
        "tkvm",
        "vlsi design",
        "thiet ke vi mach",
    ],

    # Truyền thông đa phương tiện
    "truyen-thong-da-phuong-tien": [
        "truyền thông đa phương tiện",
        "ttđpt",
        "multimedia",
        "truyen thong da phuong tien",
    ],
}


# ========== HELPER FUNCTIONS ==========

def extract_program_from_query(query: str) -> Optional[str]:
    """
    Extract program name from user query.

    Strategy:
    1. Remove university name from query to avoid confusion with program names
    2. Find all keyword matches with their positions
    3. Prioritize: earliest position → longest keyword → specific order
    4. Return the best match

    Args:
        query: User query string

    Returns:
        Program slug (e.g., "khoa-hoc-may-tinh") or None if not found

    Examples:
        >>> extract_program_from_query("điều kiện TN ngành Khoa học máy tính")
        "khoa-hoc-may-tinh"

        >>> extract_program_from_query("CTDT KHMT năm 2022")
        "khoa-hoc-may-tinh"

        >>> extract_program_from_query("số tín chỉ ngành Hệ thống thông tin trường Đại học Công nghệ Thông tin")
        "he-thong-thong-tin"  # Matches "hệ thống thông tin" BEFORE "công nghệ thông tin"

        >>> extract_program_from_query("học phí năm 2024")
        None
    """
    query_lower = query.lower()

    # STEP 1: Remove university name to avoid confusion
    # "Trường Đại học Công nghệ Thông tin" could be confused with program "Công nghệ Thông tin"
    university_names = [
        "trường đại học công nghệ thông tin",
        "đại học công nghệ thông tin",
        "đhcntt",
        "uit",
        "trường",
    ]

    cleaned_query = query_lower
    for uni_name in university_names:
        cleaned_query = cleaned_query.replace(uni_name, " ")  # Replace with space to avoid joining words

    # STEP 2: Find all matches with position and length
    # Format: (program_slug, keyword, position, length)
    matches = []

    for program_slug, keywords in PROGRAM_KEYWORDS.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            pos = cleaned_query.find(keyword_lower)
            if pos != -1:
                matches.append((program_slug, keyword, pos, len(keyword_lower)))

    # STEP 3: If no matches, return None
    if not matches:
        return None

    # STEP 4: Sort by priority
    # Priority: earliest position (ascending) → longest keyword (descending)
    # This ensures:
    # - "Hệ thống thông tin" (appears first) is prioritized over "Công nghệ thông tin" (appears later)
    # - Longer keywords are prioritized over shorter ones (e.g., "công nghệ thông tin" vs "cntt")
    matches.sort(key=lambda x: (x[2], -x[3]))  # x[2]=position, x[3]=length

    # STEP 5: Return the best match
    best_match = matches[0]
    program_slug, matched_keyword, position, length = best_match

    logger.info(f"[PROGRAM FILTER] Matched '{matched_keyword}' at position {position} → program '{program_slug}'")
    logger.info(f"[PROGRAM FILTER] Original query: '{query}'")
    logger.info(f"[PROGRAM FILTER] Cleaned query:  '{cleaned_query}'")

    return program_slug


def filter_by_program(nodes: List[NodeWithScore], program_slug: str) -> List[NodeWithScore]:
    """
    Filter nodes to only include those matching the program.

    Strategy:
    - Check if program_slug is in node.metadata['document_id']
    - Keep only matching nodes
    - If no matches found, return original list (fallback)

    Args:
        nodes: List of retrieved nodes
        program_slug: Program identifier (e.g., "khoa-hoc-may-tinh")

    Returns:
        Filtered list of nodes

    Examples:
        If program_slug = "khoa-hoc-may-tinh":
        - KEEP: "cu-nhan-nganh-khoa-hoc-may-tinh-ap-dung-tu-khoa-17-2022.md"
        - DROP: "cu-nhan-nganh-ky-thuat-may-tinh-ap-dung-tu-khoa-17-2022.md"
    """
    if not program_slug:
        return nodes

    # Filter nodes by document_id
    filtered = []
    for node in nodes:
        doc_id = node.node.metadata.get('document_id', '').lower()

        # Check if program_slug appears in document_id
        if program_slug in doc_id:
            filtered.append(node)

    # Fallback: if no matches, return original list
    # (Avoid returning empty results if filter fails)
    if not filtered:
        logger.warning(f"[PROGRAM FILTER] Warning: No documents found for program '{program_slug}', returning all results")
        return nodes

    logger.info(f"[PROGRAM FILTER] Filtered {len(nodes)} → {len(filtered)} nodes for program '{program_slug}'")
    return filtered


def apply_program_filter(query: str, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
    """
    Main entry point: Extract program from query and filter nodes.

    This is the function to call from QueryEngine._rerank()

    Args:
        query: User query
        nodes: Retrieved nodes (after reranking)

    Returns:
        Filtered nodes (or original if no program detected)

    Examples:
        >>> nodes = retrieve("điều kiện TN KHMT năm 2022")
        >>> filtered = apply_program_filter("điều kiện TN KHMT năm 2022", nodes)
        # Only returns nodes from "khoa-hoc-may-tinh" documents
    """
    # Extract program from query
    program_slug = extract_program_from_query(query)

    if not program_slug:
        logger.info(f"[PROGRAM FILTER] No program detected in query, skipping filter")
        return nodes

    logger.info(f"[PROGRAM FILTER] Detected program: {program_slug}")

    # Filter nodes
    return filter_by_program(nodes, program_slug)
