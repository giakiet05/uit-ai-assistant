"""
Pydantic schemas for structured retrieval output.

These schemas define the structured format for documents retrieved from
the knowledge base, replacing the old unstructured text format.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class RegulationDocument(BaseModel):
    """
    Structured document from retrieve_regulation tool.

    Represents a single chunk from a regulation document with
    separated metadata fields and clean content.
    """

    # Core content (metadata stripped)
    content: str = Field(
        description="Nội dung chunk (đã loại bỏ metadata prepended)"
    )

    # Metadata fields (extracted from node.metadata)
    document_id: str = Field(
        description="Tên file gốc (VD: '790_Qd_Dhcntt_28_9_22_Quy_Che_Dao_Tao')"
    )

    title: str = Field(
        description="Tiêu đề văn bản (VD: 'Quy chế đào tạo theo học chế tín chỉ...')"
    )

    regulation_code: Optional[str] = Field(
        default=None,
        description="Số hiệu văn bản (VD: '790/QĐ-ĐHCNTT')"
    )

    hierarchy: str = Field(
        description="Cấu trúc phân cấp (VD: 'CHƯƠNG 5 > Điều 33 > Khoản 1')"
    )

    effective_date: Optional[str] = Field(
        default=None,
        description="Ngày hiệu lực (ISO format: '2022-09-28')"
    )

    document_type: str = Field(
        default="Văn bản gốc",
        description="Loại văn bản (VD: 'Văn bản gốc', 'Văn bản sửa đổi', 'Văn bản thay thế')"
    )

    # Retrieval metadata
    score: float = Field(
        ge=0.0, le=1.0,
        description="Reranker score (0-1)"
    )


class CurriculumDocument(BaseModel):
    """
    Structured document from retrieve_curriculum tool.

    Represents a single chunk from a curriculum document with
    separated metadata fields and clean content.
    """

    # Core content (metadata stripped)
    content: str = Field(
        description="Nội dung chunk (đã loại bỏ metadata prepended)"
    )

    # Metadata fields
    document_id: str = Field(
        description="Tên file gốc"
    )

    title: str = Field(
        description="Tiêu đề (VD: 'Chương trình đào tạo ngành Khoa học Máy tính')"
    )

    year: Optional[int] = Field(
        default=None,
        description="Năm áp dụng chương trình (VD: 2024)"
    )

    major: Optional[str] = Field(
        default=None,
        description="Ngành học (VD: 'Khoa học Dữ liệu', 'Công nghệ Thông tin')"
    )

    program_type: Optional[Literal["Chính quy", "Từ xa"]] = Field(
        default=None,
        description="Hệ đào tạo"
    )

    program_name: Optional[str] = Field(
        default=None,
        description="Tên chương trình cụ thể (VD: 'Chương trình Tiên tiến', 'Văn bằng 2', 'Chương trình Chuẩn')"
    )

    # Retrieval metadata
    score: float = Field(
        ge=0.0, le=1.0,
        description="Reranker score (0-1)"
    )


class RegulationRetrievalResult(BaseModel):
    """Kết quả từ retrieve_regulation tool."""

    query: str = Field(
        description="Query gốc từ user"
    )

    total_retrieved: int = Field(
        description="Tổng số documents trả về"
    )

    documents: list[RegulationDocument] = Field(
        description="Danh sách regulation documents đã structured"
    )


class CurriculumRetrievalResult(BaseModel):
    """Kết quả từ retrieve_curriculum tool."""

    query: str = Field(
        description="Query gốc từ user"
    )

    total_retrieved: int = Field(
        description="Tổng số documents trả về"
    )

    documents: list[CurriculumDocument] = Field(
        description="Danh sách curriculum documents đã structured"
    )
