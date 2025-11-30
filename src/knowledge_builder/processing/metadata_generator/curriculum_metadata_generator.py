# src/processing/metadata_generator/curriculum_metadata_generator.py
from pathlib import Path
from typing import Union

from src.shared.config.settings import settings
from src.shared.llm.provider import create_llm
from .base_metadata_generator import BaseMetadataGenerator
from .metadata_models import RegulationMetadata, CurriculumMetadata, DefaultMetadata

# --- Enums defined from our analysis ---
MAJORS_ENUM = [
    "Công nghệ Thông tin", "Hệ thống Thông tin", "Khoa học Máy tính",
    "Kỹ thuật Phần mềm", "Kỹ thuật Máy tính", "Mạng máy tính và Truyền thông dữ liệu",
    "An toàn Thông tin", "Thương mại điện tử", "Khoa học Dữ liệu",
    "Trí tuệ Nhân tạo", "Thiết kế Vi mạch", "Truyền thông đa phương tiện", "Other"
]

PROGRAM_NAMES_ENUM = [
    "Chương trình Chuẩn", "Chương trình Tiên tiến", "Chương trình Liên kết quốc tế",
    "Chương trình Liên thông", "Chương trình Song ngành", "Văn bằng 2", "Other"
]

PROGRAM_TYPES_ENUM = ["Chính quy", "Từ xa"]


class CurriculumMetadataGenerator(BaseMetadataGenerator):
    """
    Generator chuyên để trích xuất metadata_generator cho các tài liệu chương trình đào tạo (curriculum).
    """

    def __init__(self):
        self.llm = create_llm(
            provider="openai",
            model=settings.processing.METADATA_GENERATION_MODEL,
            temperature=0.0
        )

    def generate(self, file_path: Path, content: str) -> Union[RegulationMetadata, CurriculumMetadata, DefaultMetadata, None]:
        """
        Triển khai logic trích xuất metadata_generator cho 'curriculum'.
        """
        print(f"INFO: Using CurriculumMetadataGenerator for {file_path.name}")

        # Format enums cho prompt
        majors_list = ", ".join([f'"{m}"' for m in MAJORS_ENUM])
        program_types_list = ", ".join([f'"{p}"' for p in PROGRAM_TYPES_ENUM])
        program_names_list = ", ".join([f'"{p}"' for p in PROGRAM_NAMES_ENUM])

        prompt = f"""
        Bạn là một chuyên viên phân tích chương trình đào tạo của trường đại học.
        Nhiệm vụ của bạn là đọc văn bản được cung cấp và trích xuất thông tin chính xác.

        **Tên file:** {file_path.name}

        **Văn bản cần phân tích:**
        ---
        {content[:8000]}
        ---

        **Yêu cầu:**
        Trích xuất các thông tin sau từ văn bản:
        - title: Tiêu đề đầy đủ của chương trình đào tạo
        - year: Năm áp dụng chương trình. QUAN TRỌNG: Ưu tiên extract từ TÊN FILE trước (VD: "khoa-19-2024" → year=2024, "khoa-2021" → year=2021). Nếu filename không có, mới lấy từ nội dung văn bản.
        - summary: Tóm tắt ngắn gọn nội dung chính (2-3 câu)
        - keywords: Các từ khóa quan trọng (5-7 từ khóa)
        - major: Ngành học chính. Phải là một trong: {majors_list}. Nếu đây là trang danh sách nhiều ngành, đặt null.
        - program_type: Hệ đào tạo. Chọn một trong: {program_types_list}, hoặc null nếu không xác định được.
        - program_name: Tên chương trình cụ thể. Chọn một trong: {program_names_list}, hoặc null nếu không xác định được.
        - is_index_page: Phân loại văn bản
          * TRUE: Nếu văn bản CHỈ là danh sách links/tên các chương trình KHÁC NHAU (index page, table of contents)
          * FALSE: Nếu văn bản có NỘI DUNG CHI TIẾT về MỘT chương trình cụ thể (môn học, chuẩn đầu ra, mô tả chi tiết)

        **Hướng dẫn chi tiết:**

        1. **Phân loại Index page vs Detail page:**
           - Index page (TRUE): CHỈ có danh sách tên/links chương trình, KHÔNG có nội dung chi tiết
             * VD: "CTĐT Khóa 2021: CNTT, HTTT, KHMT, KHDL..."
             * Với index page: major, program_type, program_name thường là null

           - Detail page (FALSE): Có nội dung CHI TIẾT về một chương trình cụ thể
             * Có mô tả: mục tiêu, chuẩn đầu ra, danh sách môn học, tín chỉ...
             * PHẢI extract major, program_type, program_name từ nội dung

        2. **Cách xác định program_type (Hệ đào tạo):**
           - "Chính quy" nếu thấy: "chính quy", "tập trung", "hình thức đào tạo: chính quy"
           - "Từ xa" nếu thấy: "từ xa", "online", "đào tạo từ xa qua mạng"
           - null nếu: văn bản KHÔNG đề cập gì về hình thức đào tạo

        3. **Cách xác định program_name (Loại chương trình):**
           - "Chương trình Tiên tiến" nếu thấy: "tiên tiến", "CTTT", "chương trình tiên tiến"
           - "Chương trình Liên kết quốc tế" nếu thấy: "liên kết", "Birmingham", "Staffordshire", "quốc tế"
           - "Chương trình Song ngành" nếu thấy: "song ngành", "hai ngành", "double major"
           - "Văn bằng 2" nếu thấy: "văn bằng 2", "văn bằng thứ 2", "bằng 2"
           - "Chương trình Chuẩn" nếu: văn bản CÓ nội dung chi tiết NHƯNG KHÔNG có các từ khóa trên
           - null nếu: đây là index page hoặc không có nội dung chi tiết

        4. **Cách xác định major (Ngành học):**
           - Tìm tên ngành trong tiêu đề hoặc nội dung
           - Khớp với danh sách: {majors_list}
           - null nếu: văn bản nói về nhiều ngành (index page)

        **Examples:**

        Example 1 - Detail page với đầy đủ thông tin:
        Filename: "content-cu-nhan-khoa-hoc-du-lieu-ap-dung-tu-khoa-15-2020.md"
        Input: "Cử nhân ngành Khoa học Dữ liệu... Hình thức đào tạo: chính quy tập trung... Chuẩn đầu ra: LO1..."
        Output: {{"year": 2020, "major": "Khoa học Dữ liệu", "program_type": "Chính quy", "program_name": "Chương trình Chuẩn", "is_index_page": false}}

        Example 2 - Detail page chương trình tiên tiến:
        Filename: "chuong-trinh-tien-tien-cntt-khoa-18-2023.md"
        Input: "Chương trình tiên tiến ngành Công nghệ Thông tin... Mục tiêu đào tạo... Danh sách môn học..."
        Output: {{"year": 2023, "major": "Công nghệ Thông tin", "program_type": "Chính quy", "program_name": "Chương trình Tiên tiến", "is_index_page": false}}

        Example 3 - Index page:
        Filename: "chuong-trinh-dao-tao-ctdt-khoa-2024.md"
        Input: "CTĐT Khóa 2024: CNTT, HTTT, KHMT, KHDL, TTĐPT..."
        Output: {{"year": 2024, "major": null, "program_type": null, "program_name": null, "is_index_page": true}}

        Example 4 - Detail page văn bằng 2:
        Filename: "van-bang-2-tu-xa-httt-khoa-2020.md"
        Input: "Văn bằng đại học thứ 2 - Hình thức từ xa... Ngành Hệ thống Thông tin..."
        Output: {{"year": 2020, "major": "Hệ thống Thông tin", "program_type": "Từ xa", "program_name": "Văn bằng 2", "is_index_page": false}}

        **Trả về JSON:**
        {{
            "title": "...",
            "year": 2021,
            "summary": "...",
            "keywords": ["keyword1", "keyword2", ...],
            "major": "...",
            "program_type": "...",
            "program_name": "...",
            "is_index_page": false
        }}

        LƯU Ý: CHỈ dùng null khi THỰC SỰ không có thông tin. Nếu văn bản có nội dung chi tiết, PHẢI extract đầy đủ.
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

            # Helper function: Convert "null" string to None
            def clean_null(value):
                if isinstance(value, str) and value.lower() in ["null", "none", "n/a"]:
                    return None
                return value

            # Tạo metadata_generator object
            metadata = CurriculumMetadata(
                document_id=file_path.name,
                category="curriculum",
                title=data.get("title", ""),
                year=data.get("year"),
                summary=data.get("summary"),
                keywords=data.get("keywords"),
                major=clean_null(data.get("major")),
                program_type=clean_null(data.get("program_type")),
                program_name=clean_null(data.get("program_name")),
                is_index_page=data.get("is_index_page", False)
            )

            print(f"SUCCESS: Extracted metadata_generator for {file_path.name}")
            print(f"  → Year: {metadata.year}")
            print(f"  → Major: {metadata.major}")
            print(f"  → Program: {metadata.program_name} ({metadata.program_type})")
            return metadata

        except Exception as e:
            print(f"ERROR: Failed to extract metadata_generator for {file_path.name}. Reason: {e}")
            import traceback
            traceback.print_exc()
            return None
