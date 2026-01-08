# src/processing/metadata_generator/metadata_models.py
from typing import Literal, Optional
from pydantic import BaseModel, Field

# --- Base Model ---
class BaseMetadata(BaseModel):
    """
    Các trường metadata chung cho tất cả các loại tài liệu.
    """
    title: str = Field(description="Tiêu đề của tài liệu.")
    category: Literal["regulation", "curriculum", "other"] = Field(description="Phân loại tài liệu.")
    is_index_page: bool = Field(default=False, description="Đánh dấu True nếu đây là trang danh sách, không có nội dung chi tiết.")

# --- Curriculum Specific Models ---
class CurriculumMetadata(BaseMetadata):
    """
    Metadata dành riêng cho tài liệu chương trình đào tạo (curriculum).
    """
    category: Literal["curriculum"] = "curriculum"
    major: Optional[str] = Field(default=None, description="Ngành học chính của chương trình đào tạo.")
    major_code: Optional[str] = Field(default=None, description="Mã ngành (VD: 'CNTT', 'KTPM', 'KHMT').")
    program_type: Optional[Literal["Chính quy", "Từ xa"]] = Field(default=None, description="Hệ đào tạo.")
    program_name: Optional[str] = Field(default=None, description="Tên chương trình cụ thể (VD: 'Chương trình Tiên tiến', 'Văn bằng 2').")
    year: Optional[int] = Field(default=None, description="Năm áp dụng chương trình đào tạo.")
    source_url: Optional[str] = Field(default=None, description="URL nguồn của trang web (nếu có).")

# --- Regulation Specific Models ---
class RegulationMetadata(BaseMetadata):
    """
    Metadata dành riêng cho tài liệu quy định (regulation).
    """
    category: Literal["regulation"] = "regulation"
    regulation_number: Optional[str] = Field(default=None, description="Số hiệu quyết định (VD: '790', '1393').")
    document_type: Optional[Literal["original", "update", "supplement"]] = Field(default=None, description="Loại văn bản quy định.")
    effective_date: Optional[str] = Field(default=None, description="Ngày hiệu lực của văn bản (YYYY-MM-DD).")
    year: Optional[int] = Field(default=None, description="Năm ban hành (extract từ effective_date).")
    pdf_file: Optional[str] = Field(default=None, description="Tên file PDF nguồn trong data/raw/regulation/.")

# --- Default Model for Other Categories ---
class DefaultMetadata(BaseMetadata):
    """
    Metadata mặc định cho các loại tài liệu khác.
    """
    category: Literal["other"] = "other"
