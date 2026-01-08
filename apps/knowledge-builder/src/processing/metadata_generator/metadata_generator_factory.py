# src/processing/metadata_generator/metadata_generator_factory.py
from typing import Type
from processing.metadata_generator.base_metadata_generator import BaseMetadataGenerator
from processing.metadata_generator.regulation_metadata_generator import RegulationMetadataGenerator
from processing.metadata_generator.curriculum_metadata_generator import CurriculumMetadataGenerator
from processing.metadata_generator.default_metadata_generator import DefaultMetadataGenerator

class MetadataGeneratorFactory:
    """
    Factory để tạo ra metadata_generator generator phù hợp dựa trên category.
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
