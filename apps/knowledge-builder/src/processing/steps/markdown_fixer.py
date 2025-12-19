"""
LLM-based markdown structure fixer.

Purpose:
- Fix deformed markdown from LlamaParse/Crawl4AI
- Normalize header hierarchy for regulation documents
- Enable perfect chunking with HierarchicalNodeSplitter

Supports multiple LLM providers via LlamaIndex:
- Gemini (default, Google AI Studio free tier: 15 RPM, 1M TPM, 200 RPD)
- OpenAI
- Ollama
"""

import time
from pathlib import Path
from typing import Optional

from llama_index.core.llms import LLM

from ...config import settings
from ...config.llm_provider import create_llm


class MarkdownFixer:
    """
    Fix markdown structure for regulation and curriculum documents using LLM.

    Supports two document types:
    - **Regulation:** Hierarchical structure (Chương → Điều → Khoản → Mục)
    - **Curriculum:** Flexible structure (fix headers, tables, bullets)

    Usage:
        # Default (Gemini from settings)
        fixer = MarkdownFixer()

        # Fix regulation
        fixed = fixer.fix_markdown(markdown_text, category="regulation")

        # Fix curriculum
        fixed = fixer.fix_markdown(markdown_text, category="curriculum")

        # Custom LLM
        
        llm = create_llm("openai", "gpt-4")
        fixer = MarkdownFixer(llm=llm)
    """

    # Prompt template for Regulation documents
    REGULATION_PROMPT = """
Bạn là chuyên gia xử lý văn bản pháp luật của trường đại học.

# NHIỆM VỤ
Sửa lại cấu trúc markdown của văn bản quy định để tuân thủ hierarchy chuẩn.

# HIERARCHY CHUẨN
```
# CHƯƠNG X                    (Level 1 - Chapter)
## Điều X                     (Level 2 - Article)
### 1. Khoản số               (Level 3 - Numbered clause)
#### a. Khoản chữ cái         (Level 4 - Lettered sub-clause)
#### Bảng X (nếu nested)      (Level 4 - Table under clause)
### Bảng X (nếu sau Điều)     (Level 3 - Table under article)
```

# QUY TẮC

## 1. Header Levels - CONSISTENCY RULE

**QUY TẮC QUAN TRỌNG:** Trong cùng nhóm (cùng Điều), nếu CÓ BẤT KỲ item nào dài → TẤT CẢ items cùng level phải là headers!

### Base Rules:
- CHƯƠNG I, CHƯƠNG II, ... → `#` (Level 1)
- Điều 1, Điều 2, ... → `##` (Level 2)
- Khoản số (1., 2., 3., ...) → `###` (Level 3)
- Khoản chữ cái (a., b., c., ...) → `####` (Level 4)

### Consistency Logic:

**Ví dụ 1: Khoản số**
```
Điều X có:
1. Khoản dài (30 từ)
2. Khoản ngắn (5 từ)
→ CẢ HAI phải là ### headers (vì có 1 cái dài)
```

**Ví dụ 2: Khoản chữ**
```
Khoản 1 có:
a. Item dài (20 từ)
b. Item ngắn (3 từ)
c. Item dài (25 từ)
→ CẢ BA phải là #### headers (vì có cái dài)
```

**Ví dụ 3: TẤT CẢ đều ngắn**
```
Danh sách ngành:
1. Khoa học máy tính (3 từ)
2. Công nghệ thông tin (3 từ)
3. Hệ thống thông tin (3 từ)
→ TẤT CẢ đều ngắn (<10 từ) → Giữ plain text (KHÔNG làm header)
```

### Threshold:
- "Dài" = >= 10 từ
- "Ngắn" = < 10 từ
- Nếu **CÓ BẤT KỲ** item >= 10 từ → **TẤT CẢ** items cùng nhóm phải là headers

### How to Apply:
1. **Scan toàn bộ Điều** trước khi quyết định
2. **Đếm từ** trong TỪNG khoản số (1., 2., 3., ...)
3. Nếu **BẤT KỲ** khoản nào >= 10 từ → **TẤT CẢ** khoản số trong Điều đó phải là `###`
4. Tương tự cho khoản chữ (a., b., c., ...) trong từng khoản số

**Ví dụ thực tế:**
```markdown
## Điều 8. Chuẩn quá trình
### 1. Sau 2 học kỳ... sinh viên phải đạt Anh văn 1... (30 từ - DÀI)
### 2. Sau 4 học kỳ... (25 từ - DÀI)
### 3. Sau 6 học kỳ... (27 từ - DÀI)
### 4. Thời điểm nộp: 2 tuần cuối tháng 7 (7 từ - NGẮN)
### 5. Không xét chuẩn (3 từ - NGẮN)
```
→ TẤT CẢ đều `###` vì khoản 1, 2, 3 dài!

## 2. Special Cases

### Title Structure (QUAN TRỌNG!):
**Vấn đề:** Văn bản có title bị tách thành NHIỀU headers:
```
# QUY ĐỊNH
## Đào tạo ngoại ngữ đối với hệ đại học chính quy
### của Trường Đại học Công nghệ Thông tin
```

**Fix:** MERGE TẤT CẢ thành 1 HEADER DUY NHẤT (viết hoa toàn bộ):
```
# QUY ĐỊNH ĐÀO TẠO NGOẠI NGỮ ĐỐI VỚI HỆ ĐẠI HỌC CHÍNH QUY CỦA TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN

*(Ban hành kèm theo Quyết định số: 547/QĐ-ĐHCNTT...)*
```

**Rules:**
1. **Identify title block:** Dòng đầu là QUY ĐỊNH/QUYẾT ĐỊNH/THÔNG BÁO + 2-3 dòng tiếp theo mô tả
2. **Merge:** Nối TẤT CẢ các dòng thành 1 header duy nhất
3. **Format:** VIẾT HOA TOÀN BỘ (uppercase)
4. **Level:** `#` (Level 1)
5. **Metadata line** *(Ban hành kèm theo...)* → Giữ nguyên italic bên dưới

**Ví dụ khác:**
```
Input:
# QUYẾT ĐỊNH
## Ban hành quy định đào tạo ngoại ngữ
## đối với hệ đại học chính quy
## của Trường Đại học Công nghệ Thông tin

Output:
# QUYẾT ĐỊNH BAN HÀNH QUY ĐỊNH ĐÀO TẠO NGOẠI NGỮ ĐỐI VỚI HỆ ĐẠI HỌC CHÍNH QUY CỦA TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN
```

### Chapter Structure:
**Vấn đề:** Chapter bị tách:
```
# CHƯƠNG I
## NHỮNG QUY ĐỊNH CHUNG
```

**Fix:** MERGE thành 1 header (uppercase):
```
# CHƯƠNG I - NHỮNG QUY ĐỊNH CHUNG
```

**Ví dụ:**
```
Input:
# CHƯƠNG II
## Chương trình giảng dạy và tổ chức đào tạo ngoại ngữ

Output:
# CHƯƠNG II - CHƯƠNG TRÌNH GIẢNG DẠY VÀ TỔ CHỨC ĐÀO TẠO NGOẠI NGỮ
```

### Other Special Cases:
- **Bold Điều** (ví dụ: `**Điều 6.**`) → Chuyển thành `## Điều 6.`
- Bảng:
  - Nếu bảng nằm sau Khoản số → `####` (Level 4)
  - Nếu bảng nằm sau Điều (no khoản) → `###` (Level 3)
  - Nếu bảng standalone → `##` (Level 2)
- Metadata sections (Căn cứ, Xét đề nghị, QUYẾT ĐỊNH) → `##` (Level 2)
- Unnumbered paragraphs giữa các khoản:
  - Nếu đoạn văn KHÔNG có số (1., 2., ...) nằm giữa các khoản có số
  - Kiểm tra context: đoạn này relate tới khoản nào?
  - Nếu là phần bổ sung cho khoản trước → Giữ nguyên plain text (KHÔNG tự gán số)
  - Nếu độc lập và quan trọng → Có thể thêm số thứ tự (ví dụ: 2.1, 2.2) NHƯNG CHỈ NẾU chắc chắn

## 3. Preserve Content
- **KHÔNG thay đổi** nội dung văn bản (giữ nguyên từ ngữ)
- **KHÔNG thay đổi** numbering (Điều 1, 2, 3...)
- **KHÔNG thay đổi** tables (giữ nguyên HTML table)
- **CHỈ SỬA** header levels (`#`, `##`, `###`, `####`)

## 4. Clean Up
- Remove empty headers (`##\\n`, `###\\n`)
- Remove excessive separators (giữ tối đa 1 separator `---` giữa các sections lớn)
- Ensure proper spacing (1 blank line giữa các sections)

# INPUT MARKDOWN
```markdown
{markdown}
```

# OUTPUT
Chỉ output markdown đã sửa, KHÔNG giải thích, KHÔNG thêm bất kỳ text nào khác ngoài markdown.
Markdown phải bắt đầu ngay từ dòng đầu tiên.
"""

    # Prompt template for Curriculum documents (SIMPLIFIED v2)
    CURRICULUM_PROMPT = """
    Bạn là chuyên gia xử lý văn bản chương trình đào tạo của trường đại học.

    # NHIỆM VỤ
    Sửa lại cấu trúc markdown của văn bản chương trình đào tạo (curriculum) để loại bỏ các lỗi rõ ràng.

    **QUAN TRỌNG:**
    - KHÔNG tự ý tạo hierarchy mới (vì mỗi khoa có format riêng)
    - CHỈ SỬA những lỗi cấu trúc RÕ RÀNG
    - GIỮ NGUYÊN nội dung, numbering, và logic tổ chức của văn bản gốc
    - ĐA SỐ bảng đã đúng format, CHỈ cần sửa nếu thấy lỗi rõ ràng

    # CÁC LỖI CẦN SỬA

    ## 1. Link text đúng ra là header
    **Pattern:** `[1. TÊN SECTION](url)` → `# 1. TÊN SECTION`

    **Ví dụ:**
    ```
    Input:
    [1. GIỚI THIỆU CHUNG](https://daa.uit.edu.vn/...)
    ## 1.1 Thông tin chung

    Output:
    # 1. GIỚI THIỆU CHUNG
    ## 1.1 Thông tin chung
    ```

    **Rule:**
    - Sections lớn (1, 2, 3) → `#` (Level 1)
    - Subsections (1.1, 3.2) → `##` (Level 2)
    - Sub-subsections (3.3.1) → `###` (Level 3)

    ## 2. Bold text đúng ra là subheader
    **Pattern:** `**Về XXX:**` hoặc `**Nhóm XXX**` → `### Về XXX` / `### Nhóm XXX`

    **Ví dụ:**
    ```
    Input:
    **Về nhận thức:**
    ‒ LO1: Nắm vững kiến thức...

    Output:
    ### Về nhận thức
    ‒ LO1: Nắm vững kiến thức...
    ```

    ## 3. Header levels không nhất quán
    **Pattern:** `# I` → `## II` → `### III` (không consistent)

    **Rule:** Normalize về cùng level nếu thấy pattern I, II, III hoặc 1.1, 1.2, 1.3

    ## 4. Bảng có vấn đề về cấu trúc
    **LƯU Ý:** ĐA SỐ bảng đã đúng format, CHỈ fix nếu thấy lỗi rõ ràng!

    **Các lỗi thường gặp:**
    - Rows thiếu separators `|` → Thêm empty cells `| | |` cho đủ số cột
    - Nested headers → Flatten thành 1 row
    - Row bắt đầu bằng `|` (merged cell) → Copy giá trị từ row trước

    **Ví dụ fix row thiếu separators:**
    ```
    Input (SAI):
    **STT** | **Mã** | **Tên** | **TC**  ← 3 separators
    ---|---|---|---
    **Nhóm môn** | **12** |              ← 2 separators (THIẾU 1!)

    Output (ĐÚNG):
    **STT** | **Mã** | **Tên** | **TC**
    ---|---|---|---
    **Nhóm môn** | **12** | |            ← 3 separators (đã thêm 1 empty cell)
    ```

    **LỖI ĐẶC BIỆT: Group header bị parse sai thành markdown header**

    **Pattern:** Header markdown (`###`, `##`) xuất hiện GIỮA bảng (sau separator `---|---`)

    **Nguyên nhân:** Scraper parse merged cell thành markdown header thay vì table row

    **Cách fix:** Convert markdown header thành table row với empty cells phù hợp số cột

    **Ví dụ:**
    ```
    Input (SAI):
    **STT** | **Tên** | **TC**
    ---|---|---
    ### I. Nhóm A                      ← SAI! Markdown header giữa bảng
    1 | Môn học 1 | 3
    2 | Môn học 2 | 4

    Output (ĐÚNG):
    **STT** | **Tên** | **TC**
    ---|---|---
    **I. Nhóm A** | |                  ← ĐÚNG! Table row với 2 empty cells
    1 | Môn học 1 | 3
    2 | Môn học 2 | 4
    ```

    **Ví dụ 2 (6 columns):**
    ```
    Input (SAI):
    **STT** | **Mã** | **Tên (VN)** | **Tên (EN)** | **LT** | **TH**
    ---|---|---|---|---|---
    ### I. Kiến thức đại cương         ← SAI!
    1 | SS007 | Triết học | Philosophy | 3 | 0

    Output (ĐÚNG):
    **STT** | **Mã** | **Tên (VN)** | **Tên (EN)** | **LT** | **TH**
    ---|---|---|---|---|---
    **I. Kiến thức đại cương** | | | | |    ← ĐÚNG! 5 empty cells cho 6 columns
    1 | SS007 | Triết học | Philosophy | 3 | 0
    ```

    **Rule:**
    - Nếu thấy `###` hoặc `##` giữa bảng → Chuyển thành table row
    - Remove prefix `###` / `##`, giữ lại text
    - Làm bold text: `**Text**`
    - Thêm empty cells `| | |` cho đủ số cột (đếm từ header)

    ## 5. Sections có title bị tách
    **Pattern:** Title bị tách thành nhiều headers → Merge thành 1 header viết hoa

    **Ví dụ:**
    ```
    Input:
    # Chương trình đào tạo song ngành
    ## ngành Thương mại điện tử

    Output:
    # CHƯƠNG TRÌNH ĐÀO TẠO SONG NGÀNH NGÀNH THƯƠNG MẠI ĐIỆN TỬ
    ```

    ## 6. Bullet list characters không đúng
    **Pattern:** En dash `‒` (U+2012) → Hyphen `-` (U+002D)

    **Ví dụ:**
    ```
    Input:
    ‒ LO1: Nắm vững kiến thức...

    Output:
    - LO1: Nắm vững kiến thức...
    ```

    # QUY TẮC CHUNG
    1. **GIỮ NGUYÊN nội dung:** Không thay đổi từ ngữ, numbering
    2. **GIỮ NGUYÊN tables:** Nội dung bảng không được thay đổi, chỉ fix structure nếu SAI RÕ RÀNG
    3. **CHỈ SỬA cấu trúc:** Header levels, link → header, bold → header, table structure (nếu sai)
    4. **Normalize bullets:** Chuyển `‒` thành `-`
    5. **KHÔNG tự ý thêm blank lines vào bảng** - Sẽ được xử lý bằng rule-based sau

    # INPUT MARKDOWN
    ```markdown
    {markdown}
    ```

    # OUTPUT
    Chỉ output markdown đã sửa, KHÔNG giải thích, KHÔNG thêm bất kỳ text nào khác ngoài markdown.
    Markdown phải bắt đầu ngay từ dòng đầu tiên.
    """

    def __init__(self, llm: Optional[LLM] = None):
        """
        Initialize markdown fixer.

        Args:
            llm: LlamaIndex LLM instance. If None, will create Gemini LLM from settings.
        """
        if llm is None:
            # Default: Create Gemini LLM from settings
            print("[MARKDOWN FIXER] No LLM provided, creating default Gemini LLM from settings")
            self.llm = create_llm(
                provider="gemini",
                model=settings.preprocessing.GEMINI_MODEL,
                temperature=settings.preprocessing.GEMINI_TEMPERATURE
            )
        else:
            # Use provided LLM
            self.llm = llm
            print(f"[MARKDOWN FIXER] Using provided LLM: {type(llm).__name__}")

        # Rate limiting config (for Gemini)
        self.rpm = settings.preprocessing.GEMINI_RPM
        self.min_delay = 60.0 / self.rpm  # Seconds between requests
        self.last_request_time = 0

        print(f"[MARKDOWN FIXER] Initialized with LLM: {type(self.llm).__name__}")
        print(f"[MARKDOWN FIXER] Rate limit: {self.rpm} RPM ({self.min_delay:.1f}s delay)")

    def fix_markdown(self, markdown_text: str, category: str = "regulation") -> str:
        """
        Fix markdown structure using LLM.

        Args:
            markdown_text: Deformed markdown from LlamaParse/Crawl4AI
            category: Document category - "regulation" or "curriculum"
                     - "regulation": Fix hierarchical structure (Chương → Điều → Khoản)
                     - "curriculum": Fix headers, tables, bullets (flexible structure)

        Returns:
            Clean markdown with correct structure

        Raises:
            Exception: If LLM API call fails or invalid category
        """
        # Validate category
        if category not in ["regulation", "curriculum"]:
            raise ValueError(f"Invalid category '{category}'. Must be 'regulation' or 'curriculum'")

        # Rate limiting
        #self._rate_limit()

        # Select prompt based on category
        if category == "regulation":
            prompt_template = self.REGULATION_PROMPT
        else:  # curriculum
            prompt_template = self.CURRICULUM_PROMPT

        # Build prompt
        prompt = prompt_template.format(markdown=markdown_text)

        # Call LLM via LlamaIndex
        try:
            response = self.llm.complete(prompt)

            # Extract text
            if not response.text:
                raise ValueError("Empty response from LLM")

            fixed_text = response.text.strip()

            # Post-processing: Remove markdown fence if LLM added it
            # Pattern: ```markdown\n...\n``` or ```\n...\n```
            if fixed_text.startswith("```"):
                lines = fixed_text.split('\n')
                # Remove first line (```markdown or ```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line (```)
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                fixed_text = '\n'.join(lines).strip()

            # Rule-based post-processing: Ensure blank lines before tables
            # This is MORE RELIABLE than LLM for this specific formatting task
            fixed_text = self._ensure_table_blank_lines(fixed_text)

            return fixed_text

        except Exception as e:
            raise Exception(f"LLM API error: {e}")

    def _ensure_table_blank_lines(self, markdown_text: str) -> str:
        """
        Rule-based post-processing: Ensure all tables have blank line before them.

        This function detects table headers (lines with `|` separators) and ensures
        there's a blank line before each table, EXCEPT when the previous line is a
        table caption (e.g., "**Bảng 1: ...**").

        Args:
            markdown_text: Markdown text (possibly from LLM)

        Returns:
            Markdown with blank lines added before tables where needed
        """
        import re

        lines = markdown_text.split('\n')
        result = []

        for i, line in enumerate(lines):
            # Detect table header: line has `|` AND next line is separator (---|---)
            # This is THE KEY: table header is followed by separator line!
            # Use .strip() to ignore leading/trailing spaces, and check for non-empty content
            # Note: Table with N columns has (N-1) separators, so >= 1 is correct (at least 2 columns)
            has_pipes = bool(line.strip() and '|' in line and line.count('|') >= 1)
            next_is_separator = False
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_is_separator = bool(re.match(r'^[\s\|:-]+$', next_line) and '-' in next_line)

            is_table_header = has_pipes and next_is_separator

            if is_table_header and i > 0:
                prev_line = lines[i - 1]

                # Check if previous line is blank
                is_prev_blank = prev_line.strip() == ''

                # Check if previous line is separator (---|---) - shouldn't happen but be safe
                is_prev_separator = bool(re.match(r'^[\s\|:-]+$', prev_line) and '-' in prev_line)

                # Add blank line if previous line is NOT blank and NOT separator
                if not is_prev_blank and not is_prev_separator:
                    result.append('')  # Add blank line

            result.append(line)

        return '\n'.join(result)

    def _rate_limit(self):
        """
        Enforce rate limiting (RPM).

        Sleeps if necessary to respect rate limits.
        """
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed
            print(f"[RATE LIMIT] Sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def batch_fix(
        self,
        input_dir: Path,
        output_dir: Optional[Path] = None,
        in_place: bool = True
    ) -> dict:
        """
        Fix all markdown files in directory.

        Args:
            input_dir: Directory with deformed markdown files
            output_dir: Directory to save fixed markdown (if in_place=False)
            in_place: If True, overwrite original files

        Returns:
            Dict with statistics: {"success": 10, "error": 2, "total": 12}
        """
        md_files = list(input_dir.glob("*.md"))
        total = len(md_files)

        if total == 0:
            print(f"[BATCH] No markdown files found in {input_dir}")
            return {"success": 0, "error": 0, "total": 0}

        print(f"[BATCH] Found {total} markdown files")
        print(f"[BATCH] Estimated time: {total * self.min_delay / 60:.1f} minutes")

        # Determine output directory
        if in_place:
            save_dir = input_dir
            print("[BATCH] Mode: In-place (will overwrite original files)")
        else:
            save_dir = output_dir or (input_dir.parent / f"{input_dir.name}_fixed")
            save_dir.mkdir(exist_ok=True)
            print(f"[BATCH] Mode: Save to new directory: {save_dir}")

        # Process files
        success_count = 0
        error_count = 0

        for idx, md_file in enumerate(md_files, 1):
            print(f"\n[{idx}/{total}] Processing: {md_file.name}")

            try:
                # Read original
                with open(md_file, encoding='utf-8') as f:
                    original = f.read()

                # Fix with Gemini
                fixed = self.fix_markdown(original)

                # Save
                output_file = save_dir / md_file.name
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(fixed)

                print(f"  ✅ Fixed and saved to {output_file}")
                success_count += 1

            except Exception as e:
                print(f"  ❌ Error: {e}")
                error_count += 1
                continue

        return {
            "success": success_count,
            "error": error_count,
            "total": total
        }
