"""
Extractor using LlamaParse for high-quality markdown conversion.
Replaces PyMuPDF, Tesseract, python-docx, openpyxl.
"""
import os
from typing import Optional
from llama_parse import LlamaParse
from .base_extractor import BaseExtractor


class LlamaExtractor(BaseExtractor):
    """
    Universal extractor sử dụng LlamaParse.
    Hỗ trợ: PDF, DOCX, XLSX, PPTX, images, và nhiều format khác.
    """
    
    def __init__(self):
        """Initialize LlamaParse với API key từ environment."""
        self.api_key = os.getenv('LLAMA_CLOUD_API_KEY')
        if not self.api_key:
            raise ValueError(
                "LLAMA_CLOUD_API_KEY not found in environment. "
                "Please set it in .env file."
            )
        
        # Initialize parser với Vietnamese support
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",  # Return markdown instead of text
            verbose=True,
            language="vi",  # Vietnamese support
        )
    
    def extract(self, file_path: str) -> str:
        """
        Extract content from file and convert to markdown.
        
        Args:
            file_path: Path to file (PDF, DOCX, XLSX, etc.)
            
        Returns:
            Markdown content or empty string on failure
        """
        try:
            if not os.path.exists(file_path):
                print(f"[ERROR] File not found: {file_path}")
                return ""
            
            print(f"[INFO] Parsing with LlamaParse: {file_path}")
            
            # Parse file synchronously
            # Note: LlamaParse has both sync and async methods
            documents = self.parser.load_data(file_path)
            
            if not documents:
                print(f"[WARNING] No content extracted from: {file_path}")
                return ""
            
            # Combine all documents into markdown
            markdown_content = "\n\n---\n\n".join([doc.text for doc in documents])
            
            print(f"[SUCCESS] Extracted {len(documents)} documents from {file_path}")
            print(f"[INFO] Content length: {len(markdown_content)} characters")
            
            return markdown_content
            
        except Exception as e:
            print(f"[ERROR] Failed to parse {file_path}: {e}")
            print(f"[INFO] Error type: {type(e).__name__}")
            return ""
    
    @staticmethod
    def get_supported_extensions():
        """Return list of supported file extensions."""
        return [
            '.pdf', '.docx', '.doc',
            '.pptx', '.ppt',
            '.xlsx', '.xls', '.csv',
            '.png', '.jpg', '.jpeg', '.gif',
            '.html', '.xml', '.txt'
        ]