"""
Flatten Table Stage - Convert markdown tables to natural text using LLM.

This stage detects all tables in markdown (including malformed ones) and
converts them to natural language descriptions for better RAG retrieval.
"""

from pathlib import Path
from typing import Dict, Any
from pipeline.core.stage import Stage
from pipeline.core.pipeline_state import PipelineState
from config.llm_provider import create_llm


class FlattenTableStage(Stage):
    """
    Flatten markdown tables to natural text using LLM.

    Why this stage is needed:
    1. Embedding models struggle with table structure (read as garbage)
    2. Chunking can split tables, losing context
    3. Natural text is better for both retrieval and LLM understanding

    Example:
    Before (Table):
        | Hệ   | TOEIC |
        |------|-------|
        | CTC  | 450   |
        | CTTN | 550   |

    After (Flattened):
        Yêu cầu TOEIC:
        - Đối với sinh viên Chương trình chuẩn (CTC): tối thiểu 450 điểm.
        - Đối với sinh viên Chương trình tài năng (CTTN): tối thiểu 550 điểm.

    This significantly improves retrieval accuracy for table-heavy documents.
    """

    def __init__(self, llm=None):
        super().__init__(
            name="flatten-table",
            is_costly=True,  # Uses LLM API
            is_idempotent=False,  # LLM may produce slightly different outputs
            description="Flatten markdown tables to natural text using LLM",
        )
        # Use provided LLM or create default (gpt-5-mini with extended timeout)
        # Note: Table flattening requires smart LLM - gpt-5-nano is too weak for this task
        # Note: Table flattening can be slow for long documents with many tables
        self.llm = llm or create_llm(
            provider="openai",
            model="gpt-5-mini",
            timeout=1800.0,  # 30 minutes timeout for long documents with many tables
        )

    def execute(
        self, input_path: Path, output_path: Path, state: PipelineState, **kwargs
    ) -> Dict[str, Any]:
        """
        Flatten all tables in markdown to natural text.

        Args:
            input_path: Path to fixed markdown (05-fixed.md)
            output_path: Path to save flattened markdown (06-flattened.md)
            state: Pipeline state
            **kwargs: Additional arguments (skip=True to skip this stage)

        Returns:
            Dict with execution status and stats
        """
        # Check if stage should be skipped
        if kwargs.get("skip", False):
            print(f"[{self.name.upper()}] Skipped (skip=True)")
            return {"executed": False, "skip_reason": "Skipped by user"}

        # Load input content
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        content = input_path.read_text(encoding="utf-8")
        print(
            f"[{self.name.upper()}] Loaded {len(content)} characters from {input_path.name}"
        )

        # Flatten tables using LLM (one-shot approach)
        print(
            f"[{self.name.upper()}] Flattening tables with {self.llm.__class__.__name__}..."
        )
        flattened_content = self._flatten_tables_with_llm(content)

        # Save output
        output_path.write_text(flattened_content, encoding="utf-8")
        print(f"[{self.name.upper()}] Saved flattened content to {output_path.name}")

        return {
            "executed": True,
            "input_length": len(content),
            "output_length": len(flattened_content),
            "output_path": str(output_path),
        }

    def _flatten_tables_with_llm(self, content: str) -> str:
        """
        Extract tables, flatten each individually with LLM, then replace in original content.

        This extract-and-replace approach:
        1. Extracts all HTML tables using regex
        2. Flattens tables in parallel using ThreadPoolExecutor (faster)
        3. Replaces tables in original content with flattened text
        
        Benefits over one-shot:
        - Works with very large documents (80KB+)
        - Each LLM call is small and fast
        - No timeout issues
        - Better error handling per table
        - Parallel processing for speed

        Args:
            content: Markdown content with tables

        Returns:
            Content with tables converted to natural text
        """
        import re
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Extract all HTML tables
        table_pattern = r'<table>.*?</table>'
        tables = list(re.finditer(table_pattern, content, re.DOTALL))
        
        if not tables:
            print(f"[FLATTEN-TABLE] No HTML tables found")
            return content
        
        print(f"[FLATTEN-TABLE] Found {len(tables)} HTML tables to flatten")
        print(f"[FLATTEN-TABLE] Processing tables in parallel (up to 5 concurrent)...")
        
        # Flatten tables in parallel
        flattened_tables = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._flatten_single_table, match.group(0), i): i
                for i, match in enumerate(tables, 1)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                table_idx = future_to_index[future]
                try:
                    flattened = future.result()
                    flattened_tables[table_idx - 1] = flattened  # 0-indexed
                except Exception as e:
                    print(f"[ERROR] Thread failed for table {table_idx}: {e}")
                    # Use original table HTML
                    flattened_tables[table_idx - 1] = tables[table_idx - 1].group(0)
        
        # Replace tables in reverse order (so positions don't shift)
        flattened_content = content
        for i in reversed(range(len(tables))):
            match = tables[i]
            flattened_content = (
                flattened_content[:match.start()] + 
                flattened_tables[i] + 
                flattened_content[match.end():]
            )
        
        print(f"\n[FLATTEN-TABLE] Completed! {len(content)} → {len(flattened_content)} chars")
        return flattened_content
    
    def _flatten_single_table(self, table_html: str, table_num: int) -> str:
        """
        Flatten a single table using LLM.
        
        Args:
            table_html: HTML table string
            table_num: Table number (for logging)
            
        Returns:
            Flattened natural text
        """
        print(f"[FLATTEN-TABLE] Table {table_num}: Processing {len(table_html)} chars...")
        
        prompt = f"""Bạn là chuyên gia xử lý văn bản học thuật. Chuyển đổi bảng HTML sau thành văn bản tự nhiên.

QUY TẮC:
- Mỗi dòng trong bảng → 1 câu văn hoàn chỉnh
- Kết hợp tiêu đề cột + hàng để tạo câu có nghĩa
- Giữ nguyên MỌI con số, ký hiệu, đơn vị
- Dùng bullet points nếu bảng có nhiều dòng
- Với rowspan/colspan: đọc kỹ cấu trúc trước khi chuyển đổi

VÍ DỤ:
Input:
<table>
<tr><th>Hệ</th><th>Điểm TOEIC</th></tr>
<tr><td>CTC</td><td>450</td></tr>
<tr><td>CTTN</td><td>550</td></tr>
</table>

Output:
Yêu cầu điểm TOEIC:
- Hệ CTC: 450 điểm
- Hệ CTTN: 550 điểm

BẢNG CẦN CHUYỂN ĐỔI:
{table_html}

VĂN BẢN ĐÃ CHUYỂN ĐỔI (chỉ trả về văn bản, không giải thích):"""

        try:
            response = self.llm.complete(prompt)
            flattened = response.text.strip()
            
            # Validate output
            if len(flattened) < 10:
                print(f"[WARNING] Table {table_num} flattened output too short, using original")
                return table_html
            
            if "<table>" in flattened:
                print(f"[WARNING] Table {table_num}: Still contains <table> tag, using original")
                return table_html
                
            print(f"[FLATTEN-TABLE] Table {table_num}: ✓ Done ({len(table_html)} → {len(flattened)} chars)")
            return flattened
            
        except Exception as e:
            print(f"[ERROR] Failed to flatten table {table_num}: {e}")
            print(f"[FLATTEN-TABLE] Using original table HTML")
            return table_html

    def get_output_filename(self) -> str:
        """Output filename for flatten-table stage."""
        return "06-flattened.md"
