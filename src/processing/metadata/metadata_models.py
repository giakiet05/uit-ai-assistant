# src/processing/metadata/metadata_models.py
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# --- Base Model ---
class BaseMetadata(BaseModel):
    """
    Các trường metadata chung cho tất cả các loại tài liệu.
    """
    document_id: str = Field(description="ID duy nhất của tài liệu, là tên file.")
    title: str = Field(description="Tiêu đề của tài liệu.")
    category: Literal["regulation", "curriculum", "other"] = Field(description="Phân loại tài liệu.")
    year: Optional[int] = Field(description="Năm ban hành/áp dụng của tài liệu.")
    summary: Optional[str] = Field(description="Tóm tắt ngắn gọn nội dung tài liệu do LLM tạo.")
    keywords: Optional[List[str]] = Field(description="Danh sách các từ khóa do LLM tạo.")
    is_index_page: bool = Field(default=False, description="Đánh dấu True nếu đây là trang danh sách, không có nội dung chi tiết.")

# --- Curriculum Specific Models ---
class CurriculumMetadata(BaseMetadata):
    """
    Metadata dành riêng cho tài liệu chương trình đào tạo (curriculum).
    """
    category: Literal["curriculum"] = "curriculum"
    major: Optional[str] = Field(default=None, description="Ngành học chính của chương trình đào tạo.")
    program_type: Optional[Literal["Chính quy", "Từ xa"]] = Field(default=None, description="Hệ đào tạo.")
    program_name: Optional[str] = Field(default=None, description="Tên chương trình cụ thể (VD: 'Chương trình Tiên tiến', 'Văn bằng 2').")

# --- Regulation Specific Models ---
class RegulationMetadata(BaseMetadata):
    """
    Metadata dành riêng cho tài liệu quy định (regulation).
    """
    category: Literal["regulation"] = "regulation"
    document_type: Optional[Literal["original", "update", "supplement"]] = Field(default=None, description="Loại văn bản quy định.")
    effective_date: Optional[str] = Field(default=None, description="Ngày hiệu lực của văn bản (YYYY-MM-DD).")
    base_regulation_code: Optional[str] = Field(default=None, description="Mã chuẩn hóa để nhóm các văn bản liên quan.")

# --- Default Model for Other Categories ---
class DefaultMetadata(BaseMetadata):
    """
    Metadata mặc định cho các loại tài liệu khác.
    """
    category: Literal["other"] = "other"
