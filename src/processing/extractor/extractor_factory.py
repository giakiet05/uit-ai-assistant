"""
Factory for creating appropriate file content extractors.
"""
import os
from typing import Type, Dict

from .base_extractor import BaseExtractor
from .pdf_extractor import PdfExtractor
from .docx_extractor import DocxExtractor
from .xlsx_extractor import XlsxExtractor

from .llama_extractor import LlamaExtractor

class ExtractorFactory:
    """A factory to create the correct extractor for a given file type."""

    _extractors: Dict[str, Type[BaseExtractor]] = {
        ".pdf": PdfExtractor,
        ".docx": DocxExtractor,
        ".xlsx": XlsxExtractor,
    }

    @classmethod
    def register_extractor(cls, extension: str, extractor_class: Type[BaseExtractor]):
        """
        Dynamically registers a new extractor class for a specific file extension.
        """
        if not extension.startswith('.'):
            raise ValueError("Extension must start with a dot (e.g., '.pdf')")
        if not issubclass(extractor_class, BaseExtractor):
            raise TypeError("extractor_class must be a subclass of BaseExtractor")
        
        print(f"[INFO] Registering extractor for extension '{extension}': {extractor_class.__name__}")
        cls._extractors[extension] = extractor_class

    @classmethod
    def get_extractor(cls, file_path: str) -> BaseExtractor:
        """
        Returns appropriate extractor for the file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Extractor instance
            
        Raises:
            ValueError: If file type not supported
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Check if LlamaParse supports this extension
        if ext in LlamaExtractor.get_supported_extensions():
            try:
                print(f"[INFO] Using LlamaParse for {ext}")
                return LlamaExtractor()
            except ValueError as e:
                # API key not set, fall back to old extractors
                print(f"[WARNING] LlamaParse not available: {e}")
                print(f"[INFO] Falling back to legacy extractor for {ext}")
                return cls._get_legacy_extractor(ext, file_path)
        
        # Unsupported file type
        raise ValueError(f"No extractor available for file type: {ext}")
    
    @classmethod
    def _get_legacy_extractor(cls, ext: str, file_path: str) -> BaseExtractor:
        """
        Get legacy extractor as fallback.
        """
        legacy_mapping = {
            '.pdf': PdfExtractor,
            '.docx': DocxExtractor,
            '.doc': DocxExtractor,
            '.xlsx': XlsxExtractor,
            '.xls': XlsxExtractor,
        }
        
        extractor_class = legacy_mapping.get(ext)
        if extractor_class:
            return extractor_class()
        
        raise ValueError(f"No legacy extractor for: {ext}")