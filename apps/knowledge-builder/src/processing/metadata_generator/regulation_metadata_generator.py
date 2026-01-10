# src/processing/metadata_generator/regulation_metadata_generator.py
import json
import re
from pathlib import Path
from typing import Union, Optional, Dict

from config.settings import settings
from config.llm_provider import create_llm
from processing.metadata_generator.base_metadata_generator import BaseMetadataGenerator
from processing.metadata_generator.metadata_models import RegulationMetadata, CurriculumMetadata, DefaultMetadata

class RegulationMetadataGenerator(BaseMetadataGenerator):
    """
    Generator chuyên để trích xuất metadata cho các tài liệu quy định (regulation).
    Sử dụng LLM để trích xuất có cấu trúc và áp dụng logic để đảm bảo tính nhất quán.
    """

    def __init__(self):
        # Khởi tạo LLM thông qua LlamaIndex
        self.llm = create_llm(
            provider="openai",
            model=settings.processing.METADATA_GENERATION_MODEL
        )

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
            # Test format: 05-quy-dinh__828_qd-dhcntt_xxx -> Match phần sau __
            # Raw format: 828_qd-dhcntt_xxx -> Match từ đầu

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

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract effective date từ filename.
        VD: "828_qd-dhcntt_04-10-2022_..." -> "2022-10-04"
        VD: "108-qd-dhcntt15-3-2019_..." -> "2019-03-15"
        VD: "790-qd-dhcntt_28-9-22_..." -> "2022-09-28"
        Pattern: DD-MM-YYYY hoặc DD-MM-YY (có thể thiếu underscore)
        """
        # Pattern: DD-MM-YYYY hoặc DD-MM-YY với separator linh hoạt (_, -, hoặc không có)
        # Match: _04-10-2022_, 15-3-2019_, 28-9-22_
        pattern = r'[-_]?(\d{1,2})-(\d{1,2})-(\d{2,4})(?:_|$)'
        match = re.search(pattern, filename)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)

            # Convert YY -> YYYY (assume 20YY for years < 100)
            if len(year) == 2:
                year = f"20{year}"

            date_str = f"{year}-{month}-{day}"
            print(f"   Extracted date from filename: {date_str}")
            return date_str
        return None

    def generate(self, file_path: Path, content: str) -> Union[RegulationMetadata, CurriculumMetadata, DefaultMetadata, None]:
        """
        Triển khai logic trích xuất metadata cho 'regulation'.
        Sử dụng LLM để extract title, document_type, is_index_page.
        Extract regulation_number, effective_date, year, pdf_file từ filename và filesystem.
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
    "document_type": "original" hoặc "update",
    "is_index_page": false
}}

**HƯỚNG DẪN CHI TIẾT:**

1. **title:** Tiêu đề đầy đủ của văn bản (extract từ header)

2. **document_type:**
   - "original": Văn bản ban hành MỚI, quy định lần đầu
   - "update": Văn bản SỬA ĐỔI/BỔ SUNG văn bản khác

3. **is_index_page:**
   - true: Trang danh sách/mục lục
   - false: Văn bản chi tiết

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

            # Extract regulation_number từ document directory name (không phải filename 05-fixed.md)
            # VD: file_path = "/path/to/790-qd-dhcntt_28-9-22_quy_che_dao_tao/05-fixed.md"
            # -> document_dir = "790-qd-dhcntt_28-9-22_quy_che_dao_tao"
            document_dir_name = file_path.parent.name

            regulation_number = None
            filename_code = self._extract_regulation_code(document_dir_name, from_filename=True)
            if filename_code:
                # Extract chỉ số (VD: "790" từ "790/QĐ-ĐHCNTT")
                regulation_number = filename_code.split("/")[0]
                print(f"   Extracted regulation_number: {regulation_number}")

            # Extract effective_date từ document directory name
            effective_date = self._extract_date_from_filename(document_dir_name)
            year = None
            if effective_date:
                year = int(effective_date.split("-")[0])
                print(f"   Extracted effective_date: {effective_date}, year: {year}")

            # Find PDF file in raw/regulation/
            pdf_file = None
            raw_regulation_dir = settings.paths.DATA_DIR / "raw" / "regulation"
            if raw_regulation_dir.exists():
                # Try to find PDF with document directory name
                # VD: "790-qd-dhcntt_28-9-22_quy_che_dao_tao" -> "790-qd-dhcntt_28-9-22_quy_che_dao_tao.pdf"
                pdf_path = raw_regulation_dir / f"{document_dir_name}.pdf"
                if pdf_path.exists():
                    pdf_file = pdf_path.name
                    print(f"   Found PDF file: {pdf_file}")

            # Tạo metadata object
            metadata = RegulationMetadata(
                category="regulation",
                title=data.get("title", ""),
                regulation_number=regulation_number,
                document_type=data.get("document_type"),
                effective_date=effective_date,
                year=year,
                pdf_file=pdf_file,
                is_index_page=data.get("is_index_page", False)
            )

            print(f"SUCCESS: Extracted metadata for {file_path.name}")
            print(f"  -> Regulation Number: {metadata.regulation_number}")
            print(f"  -> Document Type: {metadata.document_type}")
            print(f"  -> PDF File: {metadata.pdf_file}")
            return metadata

        except Exception as e:
            print(f"ERROR: Failed to extract metadata_generator for {file_path.name}. Reason: {e}")
            import traceback
            traceback.print_exc()
            return None
