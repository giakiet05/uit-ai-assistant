# src/processing/metadata/default_metadata_generator.py
from pathlib import Path
from typing import Union
from .base_metadata_generator import BaseMetadataGenerator
from .metadata_models import RegulationMetadata, CurriculumMetadata, DefaultMetadata

class DefaultMetadataGenerator(BaseMetadataGenerator):
    """
    Generator mặc định cho các category không xác định.
    Chỉ trích xuất các thông tin cơ bản nhất.
    """

    def generate(self, file_path: Path, content: str) -> Union[RegulationMetadata, CurriculumMetadata, DefaultMetadata, None]:
        """
        Triển khai logic trích xuất metadata mặc định.
        """
        print(f"DEBUG: Using DefaultMetadataGenerator for {file_path.name}")

        # Placeholder implementation for basic metadata
        metadata = DefaultMetadata(
            document_id=file_path.name,
            title=f"Placeholder Title for {file_path.stem}",
            category="other",
            year=None,
            summary="This is a default placeholder summary.",
            keywords=["placeholder"],
        )
        return metadata
