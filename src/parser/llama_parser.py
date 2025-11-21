"""
LlamaParse integration for parsing various file formats to markdown.
"""
import os
from typing import Optional
from llama_parse import LlamaParse

class LlamaFileParser:
    """Parser sử dụng LlamaParse để chuyển đổi files sang markdown."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('LLAMA_CLOUD_API_KEY')
        if not self.api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY is required")
        
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            verbose=True,
            language="vi",
        )
    
    async def parse_file(self, file_path: str) -> Optional[str]:
        """Parse một file thành markdown."""
        try:
            if not os.path.exists(file_path):
                print(f"[ERROR] File không tồn tại: {file_path}")
                return None
            
            print(f"[INFO] Parsing file với LlamaParse: {file_path}")
            documents = await self.parser.aload_data(file_path)
            
            if not documents:
                print(f"[WARNING] Không parse được nội dung từ: {file_path}")
                return None
            
            markdown_content = "\n\n".join([doc.text for doc in documents])
            print(f"[SUCCESS] Parsed {len(documents)} documents từ {file_path}")
            return markdown_content
            
        except Exception as e:
            print(f"[ERROR] Lỗi khi parse {file_path}: {e}")
            return None
    
    def get_supported_extensions(self) -> list:
        """Trả về list các extension được hỗ trợ."""
        return [
            '.pdf', '.docx', '.doc', '.pptx', '.ppt',
            '.xlsx', '.xls', '.csv',
            '.png', '.jpg', '.jpeg', '.gif',
            '.html', '.xml', '.txt'
        ]
