"""
This package contains modules for extracting text content from various file formats.

Key components:
- BaseExtractor: The abstract base class for all file extractors.
- ExtractorFactory: A factory for creating parser instances based on file extension.
- extract_all, extract_domain, extract_folder: Core functions to run the extraction process.
"""

from .base_parser import BaseParser
from .parser_factory import ParserFactory

__all__ = [
    "BaseParser",
    "ParserFactory",
]
