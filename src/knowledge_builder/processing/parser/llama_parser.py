"""
LlamaParse-based parser for converting documents to markdown.

Supports PDF, DOCX, XLSX with advanced OCR, table extraction, and layout handling.
Uses LlamaCloud API for high-quality document conversion.
"""
from pathlib import Path
from typing import List
from llama_cloud_services import LlamaParse

from .base_parser import BaseParser
from src.shared.config import settings


class LlamaParser(BaseParser):
    """
    High-quality document parser using LlamaCloud's LlamaParse service.

    Features:
    - Advanced OCR for scanned PDFs (high_res_ocr)
    - Intelligent table detection and HTML formatting
    - Multi-column layout handling
    - Agent-powered parsing for complex documents
    - Support for PDF, DOCX, XLSX, and more

    This parser extends BaseExtractor and can be used as a drop-in replacement
    for PDFExtractor, DOCXExtractor, etc.

    Example:
        >>> parser = LlamaParser()
        >>> markdown = parser.parse("document.pdf")
        >>> # Returns: "# Document Title\\n\\nContent..."
    """

    # Supported file extensions
    SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".xlsx", ".doc", ".xls", ".pptx"]

    def __init__(
        self,
        parse_mode: str = "parse_page_with_agent",
        model: str = "openai-gpt-4-1-mini",
        high_res_ocr: bool = True,
        adaptive_long_table: bool = True,
        outlined_table_extraction: bool = True,
        output_tables_as_HTML: bool = True
    ):
        """
        Initialize LlamaParse parser.

        Args:
            parse_mode: Parsing mode for LlamaParse.
                       "parse_page_with_agent" (default): AI-powered parsing
                       "basic": Faster, simpler parsing
            model: LLM model for agent-powered parsing.
            high_res_ocr: Enable high-resolution OCR for scanned documents.
                         Slower but more accurate for images/scans.
            adaptive_long_table: Automatically detect and adapt long tables.
            outlined_table_extraction: Extract tables with borders.
            output_tables_as_HTML: Format tables as HTML in markdown output.

        Raises:
            ValueError: If API key not found in settings or provided.
        """
        # Get API key from settings or parameter
        self.api_key = settings.credentials.LLAMA_CLOUD_API_KEY

        if not self.api_key:
            raise ValueError(
                "LLAMA_CLOUD_API_KEY not found. "
                "Please set LLAMA_CLOUD_API_KEY in .env file or pass to constructor."
            )

        # Initialize LlamaParse client
        try:
            self.parser = LlamaParse(
                api_key=self.api_key,
                parse_mode=parse_mode,
                model=model,
                high_res_ocr=high_res_ocr,
                adaptive_long_table=adaptive_long_table,
                outlined_table_extraction=outlined_table_extraction,
                output_tables_as_HTML=output_tables_as_HTML
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize LlamaParse: {str(e)}. "
                "Please check API key and llama-cloud-services installation."
            ) from e

    def parse(self, file_path: str) -> str:
        """
        Extract text content from file using LlamaParse.

        Implements BaseExtractor.extract() interface.

        Args:
            file_path: Absolute path to file (.pdf, .docx, .xlsx, etc.)

        Returns:
            Extracted markdown content as string

        Raises:
            ValueError: If file type not supported
            FileNotFoundError: If file doesn't exist
            RuntimeError: If parsing fails

        Example:
            >>> parser = LlamaParser()
            >>> content = parser.parse("/path/to/document.pdf")
            >>> print(content[:100])
            '# QUYẾT ĐỊNH\\n\\nVề việc ban hành quy chế...'
        """
        path = Path(file_path)

        # Validate file extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file is not empty
        if path.stat().st_size == 0:
            raise ValueError(f"File is empty: {file_path}")

        try:
            print(f"[INFO] Parsing {path.name} with LlamaParse...")

            # Parse document
            result = self.parser.parse(str(path))

            # Extract markdown (full document, not split by page)
            markdown_docs = result.get_markdown_documents(split_by_page=False)

            if not markdown_docs:
                raise RuntimeError(
                    f"LlamaParse returned no content for: {path.name}"
                )

            # Get markdown text from first document
            markdown_text = markdown_docs[0].text

            if not markdown_text or not markdown_text.strip():
                raise RuntimeError(
                    f"LlamaParse returned empty content for: {path.name}"
                )

            print(f"[SUCCESS] Parsed {path.name} ({len(markdown_text)} chars)")

            return markdown_text

        except Exception as e:
            # Re-raise with more context
            raise RuntimeError(
                f"Failed to parse {path.name}: {str(e)}"
            ) from e

    def extract_batch(self, file_paths: List[str]) -> List[str]:
        """
        Parse multiple files in batch for better efficiency.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of markdown strings (same order as input)

        Example:
            >>> parser = LlamaParser()
            >>> results = parser.extract_batch([
            ...     "file1.pdf",
            ...     "file2.pdf",
            ...     "file3.docx"
            ... ])
            >>> len(results)
            3
        """
        # Validate all files first
        valid_paths = []
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                print(f"[WARNING] Skipping non-existent file: {file_path}")
                continue
            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                print(f"[WARNING] Skipping unsupported file: {file_path}")
                continue
            valid_paths.append(str(path))

        if not valid_paths:
            return []

        try:
            print(f"[INFO] Batch parsing {len(valid_paths)} files with LlamaParse...")

            # Batch parse
            results = self.parser.parse(valid_paths)

            # Extract markdown from each result
            markdown_list = []
            for i, result in enumerate(results):
                markdown_docs = result.get_markdown_documents(split_by_page=False)

                if markdown_docs and markdown_docs[0].text:
                    markdown_list.append(markdown_docs[0].text)
                    print(f"[SUCCESS] Parsed file {i+1}/{len(valid_paths)}")
                else:
                    markdown_list.append("")
                    print(f"[WARNING] Empty content for file {i+1}/{len(valid_paths)}")

            return markdown_list

        except Exception as e:
            raise RuntimeError(
                f"Batch parsing failed: {str(e)}"
            ) from e

    def supports_file(self, file_path: str) -> bool:
        """
        Check if this parser supports the given file type.

        Args:
            file_path: Path to file

        Returns:
            True if file extension is supported

        Example:
            >>> parser = LlamaParser()
            >>> parser.supports_file("document.pdf")
            True
            >>> parser.supports_file("image.png")
            False
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def __repr__(self) -> str:
        """String representation."""
        return f"<LlamaParser(model={self.parser.model if hasattr(self.parser, 'model') else 'unknown'})>"
