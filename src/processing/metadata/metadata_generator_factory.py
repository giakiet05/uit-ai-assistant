# src/processing/metadata/metadata_generator_factory.py
from typing import Type
from .base_metadata_generator import BaseMetadataGenerator
from .regulation_metadata_generator import RegulationMetadataGenerator
from .curriculum_metadata_generator import CurriculumMetadataGenerator
from .default_metadata_generator import DefaultMetadataGenerator

class MetadataGeneratorFactory:
    """
    Factory để tạo ra metadata generator phù hợp dựa trên category.
    """
    _generators = {
        "regulation": RegulationMetadataGenerator,
        "curriculum": CurriculumMetadataGenerator,
        "other": DefaultMetadataGenerator,
    }

    @classmethod
    def get_generator(cls, category: str) -> BaseMetadataGenerator:
        """
        Lấy một instance của generator phù hợp với category.

        Args:
            category (str): Tên của category (e.g., "regulation", "curriculum").

        Returns:
            Một instance của một class kế thừa từ BaseMetadataGenerator.
        """
        generator_class: Type[BaseMetadataGenerator] = cls._generators.get(category, DefaultMetadataGenerator)
        return generator_class()
