# src/processing/metadata_generator/regulation_metadata_generator.py
import json
import re
from pathlib import Path
from typing import Union, Optional, Dict

from src.config.settings import settings
from src.llm.provider import create_llm
from .base_metadata_generator import BaseMetadataGenerator
from .metadata_models import RegulationMetadata, CurriculumMetadata, DefaultMetadata

# Path to the lookup file for base regulation codes
REGULATION_CODE_LOOKUP_PATH = settings.paths.DATA_DIR / "regulation_codes.json"

class RegulationMetadataGenerator(BaseMetadataGenerator):
    """
    Generator chuyên để trích xuất metadata_generator cho các tài liệu quy định (regulation).
    Sử dụng LLM để trích xuất có cấu trúc và áp dụng logic để đảm bảo tính nhất quán.
    """

    def __init__(self):
        # Khởi tạo LLM thông qua LlamaIndex
        self.llm = create_llm(
            provider="openai",
            model=settings.processing.METADATA_GENERATION_MODEL,
            temperature=0.0
        )
        self._load_regulation_codes()

    def _load_regulation_codes(self) -> None:
        """Tải 'sổ tay tra cứu' mã quy định từ file JSON."""
        if REGULATION_CODE_LOOKUP_PATH.exists():
            try:
                with open(REGULATION_CODE_LOOKUP_PATH, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.regulation_codes: Dict[str, str] = json.loads(content)
                    else:
                        self.regulation_codes = {}
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"  ⚠️  Failed to load regulation_codes.json, starting fresh")
                self.regulation_codes = {}
        else:
            self.regulation_codes = {}

    def _save_regulation_codes(self) -> None:
        """Lưu lại 'sổ tay tra cứu' mã quy định vào file JSON."""
        with open(REGULATION_CODE_LOOKUP_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.regulation_codes, f, ensure_ascii=False, indent=4)

    def _extract_regulation_code(self, text: str, from_filename: bool = False) -> Optional[str]:
        """
        Trích xuất số hiệu văn bản từ text (VD: '828/QĐ-ĐHCNTT', '1234/QĐ-BGH').
        Sử dụng regex để tìm pattern phổ biến của số hiệu quyết định.

        Args:
            text: Text to extract from
            from_filename: If True, expect underscore format (828_qd-dhcntt)
                          If False, expect slash format (828/QĐ-ĐHCNTT)
        """
        if from_filename:
            # Pattern cho filename - Support nhiều loại văn bản:
            # Test format: 05-quy-dinh__828_qd-dhcntt_xxx → Match phần sau __
            # Raw format: 828_qd-dhcntt_xxx → Match từ đầu

            # Try 1: Match sau __ (test format)
            pattern_with_prefix = r'__(\d+)[-_]([a-z]+)-([a-z\u00C0-\u1EF9]+(?:-[a-z\u00C0-\u1EF9]+)?)'
            match = re.search(pattern_with_prefix, text, re.IGNORECASE)

            # Try 2: Match từ đầu (raw format) - CHỈ khi không có __
            if not match and '__' not in text:
                pattern_no_prefix = r'^(\d+)[-_]([a-z]+)-([a-z\u00C0-\u1EF9]+(?:-[a-z\u00C0-\u1EF9]+)?)'
                match = re.search(pattern_no_prefix, text, re.IGNORECASE)

            if match:
                # Convert sang format: 828/QĐ-ĐHCNTT hoặc 35/TB-ĐHCNTT
                number = match.group(1)
                doc_type = match.group(2).upper()  # QD, TB, CV, TT, ...
                organization = match.group(3).upper()
                return f"{number}/{doc_type}-{organization}"
        else:
            # Pattern cho content: số/QĐ-XXX hoặc số/QĐ-ĐHCNTT-XXX
            pattern = r'(\d+/Q[ĐD]-[A-Z\u00C0-\u1EF9]+(?:-[A-Z\u00C0-\u1EF9]+)?)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Trả về match đầu tiên (thường là số hiệu chính của văn bản)
                return matches[0]

        return None

    def _extract_base_code_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract regulation code từ filename.
        VD: "828_qd-dhcntt_..." → "828/QĐ-ĐHCNTT"
        """
        result = self._extract_regulation_code(filename, from_filename=True)
        if result:
            print(f"  ✓ Extracted base code from filename: {result}")
        return result

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract effective date từ filename.
        VD: "828_qd-dhcntt_04-10-2022_..." → "2022-10-04"
        VD: "108-qd-dhcntt15-3-2019_..." → "2019-03-15"
        Pattern: DD-MM-YYYY (có thể thiếu underscore)
        """
        # Pattern: DD-MM-YYYY với separator linh hoạt (_, -, hoặc không có)
        # Match: _04-10-2022_, 15-3-2019_, -15-3-2019_
        pattern = r'[-_]?(\d{1,2})-(\d{1,2})-(\d{4})(?:_|$)'
        match = re.search(pattern, filename)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            date_str = f"{year}-{month}-{day}"
            print(f"  ✓ Extracted date from filename: {date_str}")
            return date_str
        return None

    def generate(self, file_path: Path, content: str) -> Union[RegulationMetadata, CurriculumMetadata, DefaultMetadata, None]:
        """
        Triển khai logic trích xuất metadata_generator cho 'regulation'.
        SINGLE LLM CALL - Extract tất cả metadata_generator including base_regulation_code.
        """
        print(f"INFO: Using RegulationMetadataGenerator for {file_path.name}")

        prompt = f"""
Bạn là chuyên viên phân tích văn bản pháp lý.

**FILENAME:** {file_path.name}

**NỘI DUNG VĂN BẢN:**
---
{content[:8000]}
---

**YÊU CẦU:** Trích xuất JSON với format:

{{
    "title": "...",
    "year": 2024,
    "summary": "...",
    "keywords": ["..."],
    "document_type": "original" hoặc "update",
    "effective_date": "2024-01-01",
    "is_index_page": false,
    "base_regulation_code": "828/QĐ-ĐHCNTT" hoặc null
}}

**HƯỚNG DẪN CHI TIẾT:**

1. **document_type:**
   - "original": Văn bản ban hành MỚI, quy định lần đầu
   - "update": Văn bản SỬA ĐỔI/BỔ SUNG văn bản khác

2. **base_regulation_code** (QUAN TRỌNG):

   **Nếu document_type = "original":**
   - KHÔNG tìm trong phần "Căn cứ" (đó là các văn bản khác)
   - CHỈ tìm số hiệu của CHÍNH VĂN BẢN NÀY:
     * Dòng "Số: XXX/QĐ-YYY" ở ĐẦU văn bản (trước phần "Căn cứ")
     * HOẶC từ FILENAME (VD: filename có "147-qd-dhcntt" → "147/QĐ-DHCNTT")
   - Format: "147/QĐ-DHCNTT", "828/QĐ-ĐHCNTT"
   - Nếu không tìm thấy → null

   **Nếu document_type = "update":**
   - Bước 1: Xác định TIÊU ĐỀ/CHỦ ĐỀ của văn bản này (VD: "đào tạo ngoại ngữ")
   - Bước 2: Đọc phần "CĂN CỨ" (các dòng bắt đầu bằng "Căn cứ Quyết định...")
   - Bước 3: So sánh chủ đề văn bản với NỘI DUNG của các quyết định trong phần Căn cứ
   - Bước 4: Chọn quyết định có chủ đề GẦN GIỐNG NHẤT (cùng lĩnh vực, có thể khác vài chữ)
   - Bước 5: Trích xuất số hiệu từ dòng đó
   - Format: "828/QĐ-ĐHCNTT"
   - Nếu không tìm thấy văn bản tương tự → null

**VÍ DỤ:**

VD1 - Original:
Tiêu đề: "Quy định đào tạo ngoại ngữ..."
Số: 828/QĐ-ĐHCNTT
→ base_regulation_code: "828/QĐ-ĐHCNTT"

VD2 - Update:
Tiêu đề: "Sửa đổi Quy định đào tạo ngoại ngữ..."
Phần Căn cứ:
- Căn cứ Quyết định số 134/2006/QĐ-TTg về việc thành lập trường...  ← KHÔNG (chủ đề khác)
- Căn cứ Quyết định số 828/QĐ-ĐHCNTT về quy định đào tạo ngoại ngữ...  ← GẦN GIỐNG! (cùng "đào tạo ngoại ngữ")
→ base_regulation_code: "828/QĐ-ĐHCNTT"

3. **is_index_page:** true nếu là trang danh sách, false nếu là văn bản chi tiết

CHỈ TRẢ VỀ JSON, KHÔNG GIẢI THÍCH.
        """

        try:
            response = self.llm.complete(prompt)
            response_text = response.text.strip()

            # Parse JSON response
            import json
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)

            # Merge "supplement" vào "update" nếu LLM trả về
            if data.get("document_type") == "supplement":
                data["document_type"] = "update"

            # Extract base_regulation_code từ LLM response
            llm_base_code = data.get("base_regulation_code")

            # Validate và clean
            if llm_base_code and isinstance(llm_base_code, str):
                llm_base_code = llm_base_code.strip()
                if llm_base_code.lower() in ["null", "none", "n/a"]:
                    llm_base_code = None
                elif "/" not in llm_base_code:
                    print(f"  ⚠️  Invalid base_regulation_code format: '{llm_base_code}' → Using filename fallback")
                    llm_base_code = None

            # IMPORTANT: Với văn bản "original", PRIORITIZE filename extraction
            # LLM có thể nhầm lẫn giữa các số hiệu trong văn bản
            filename_code = self._extract_base_code_from_filename(file_path.stem)

            if data.get("document_type") == "original" and filename_code:
                # Original doc: LUÔN dùng filename (chính xác nhất)
                llm_base_code = filename_code
                print(f"  → Original doc: Using filename code: {filename_code}")
            elif not llm_base_code:
                # Fallback: LLM không trả về hoặc invalid → dùng filename
                print(f"  ⚠️  LLM did not return valid base_regulation_code, using filename...")
                llm_base_code = filename_code

            # PRIORITIZE: Extract date from filename (chính xác hơn LLM)
            filename_date = self._extract_date_from_filename(file_path.stem)
            if filename_date:
                data["effective_date"] = filename_date
                # Extract year from date
                data["year"] = int(filename_date.split("-")[0])

            # Final base_regulation_code
            final_base_code = None
            if llm_base_code:
                # Extract số hiệu (VD: "828" từ "828/QĐ-ĐHCNTT")
                base_num = llm_base_code.split("/")[0]

                # Check lookup table
                if base_num in self.regulation_codes:
                    final_base_code = self.regulation_codes[base_num]
                    print(f"  → Using existing base code from lookup: {final_base_code}")
                else:
                    final_base_code = base_num
                    self.regulation_codes[base_num] = base_num
                    self._save_regulation_codes()
                    print(f"  → New base code registered: {final_base_code}")

            # Tạo metadata_generator object
            metadata = RegulationMetadata(
                document_id=file_path.name,
                category="regulation",
                title=data.get("title", ""),
                year=data.get("year"),
                summary=data.get("summary"),
                keywords=data.get("keywords"),
                document_type=data.get("document_type"),
                effective_date=data.get("effective_date"),
                is_index_page=data.get("is_index_page", False),
                base_regulation_code=final_base_code
            )

            print(f"SUCCESS: Extracted metadata_generator for {file_path.name}")
            print(f"  → Document Type: {metadata.document_type}")
            print(f"  → Base Regulation Code: {metadata.base_regulation_code}")
            return metadata

        except Exception as e:
            print(f"ERROR: Failed to extract metadata_generator for {file_path.name}. Reason: {e}")
            import traceback
            traceback.print_exc()
            return None
