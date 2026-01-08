"""
Factory for creating appropriate file content extractors.
"""
import os
from typing import Type, Dict

from processing.parser.base_parser import BaseParser
from processing.parser.pdf_parser import PdfParser
from processing.parser.docx_parser import DocxParser
# XLSX not supported - use SQL database instead for structured data

class ParserFactory:
    """A factory to create the correct parser for a given file type."""

    _parsers: Dict[str, Type[BaseParser]] = {
        ".pdf": PdfParser,
        ".docx": DocxParser,
        # .xlsx intentionally not included - structured data should go to SQL DB
    }

    @classmethod
    def register_parser(cls, extension: str, extractor_class: Type[BaseParser]):
        """
        Dynamically registers a new parser class for a specific file extension.
        """
        if not extension.startswith('.'):
            raise ValueError("Extension must start with a dot (e.g., '.pdf')")
        if not issubclass(extractor_class, BaseParser):
            raise TypeError("extractor_class must be a subclass of BaseExtractor")
        
        print(f"[INFO] Registering parser for extension '{extension}': {extractor_class.__name__}")
        cls._parsers[extension] = extractor_class

    @classmethod
    def get_parser(cls, file_path: str, use_llamaparse: bool = True) -> BaseParser:
        """
        Instantiates and returns the appropriate parser for the given file path.

        Args:
            file_path: Path to file to extract
            use_llamaparse: If True, try LlamaParser first (requires LLAMA_CLOUD_API_KEY)

        Priority:
            1. LlamaParser (if use_llamaparse=True and API key configured)
            2. Default extractors (PDF, DOCX, XLSX)

        Raises:
            ValueError: If the file extension is not supported by any parser.

        Example:
            >>> # Use LlamaParser (default)
            >>> parser = ParserFactory.get_parser("document.pdf")
            >>>
            >>> # Force use of default extractors
            >>> parser = ParserFactory.get_parser("document.pdf", use_llamaparse=False)
        """
        # Try LlamaParse first if enabled
        if use_llamaparse:
            try:
                from processing.parser.llama_parser import LlamaParser
                llama = LlamaParser()
                if llama.supports_file(file_path):
                    return llama
            except ValueError:
                # API key not configured, fall back to default extractors
                pass
            except Exception as e:
                # Other initialization errors, log and fall back
                print(f"[WARNING] LlamaParser initialization failed: {e}. Using default extractors.")

        # Fall back to default extractors
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        extractor_class = cls._parsers.get(extension)

        if extractor_class:
            return extractor_class()
        else:
            raise ValueError(f"Unsupported file extension: '{extension}'")
