# src/processing/metadata_generator/base_metadata_generator.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Union
from .metadata_models import BaseMetadata, RegulationMetadata, CurriculumMetadata, DefaultMetadata

class BaseMetadataGenerator(ABC):
    """
    Abstract base class for metadata_generator generators.
    Mỗi generator chuyên biệt cho một category sẽ kế thừa từ class này.
    """

    @abstractmethod
    def generate(self, file_path: Path, content: str) -> Union[RegulationMetadata, CurriculumMetadata, DefaultMetadata, None]:
        """
        Hàm chính để tạo metadata_generator từ nội dung file.

        Args:
            file_path (Path): Đường dẫn đến file đang được xử lý.
            content (str): Nội dung của file.

        Returns:
            Một instance của Pydantic model (RegulationMetadata, CurriculumMetadata, etc.) hoặc None nếu thất bại.
        """
        pass
