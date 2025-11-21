"""
LLM-based markdown structure fixer using Google Gemini.

Uses Google AI Studio free tier:
- Model: gemini-2.0-flash-exp
- 15 RPM (requests per minute)
- 1M TPM (tokens per minute)
- 200 RPD (requests per day)

Purpose:
- Fix deformed markdown from LlamaParse/Crawl4AI
- Normalize header hierarchy for regulation documents
- Enable perfect chunking with HierarchicalNodeSplitter
"""

import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from src.config.settings import settings


class GeminiMarkdownFixer:
    """
    Fix regulation markdown structure using Gemini LLM.

    Converts deformed markdown (from PDF parsing) into clean, hierarchical structure:
    - # CHƯƠNG X (Level 1 - Chapter)
    - ## Điều X (Level 2 - Article)
    - ### 1. Khoản số (Level 3 - Numbered clause, if >= 15 words)
    - #### a. Khoản chữ (Level 4 - Lettered sub-clause, if >= 15 words)
    """

    # Prompt template for Gemini
    PROMPT_TEMPLATE = """
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

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini markdown fixer.

        Args:
            api_key: Google API key (if None, will use from settings)
        """
        # Get API key
        api_key = api_key or settings.credentials.GOOGLE_API_KEY
        if not api_key:
            raise ValueError(
                "Google API key not found. "
                "Set GOOGLE_API_KEY in .env or pass api_key parameter."
            )

        # Initialize client (NEW API)
        self.client = genai.Client(api_key=api_key)

        # Load model config from settings
        self.model_name = settings.preprocessing.GEMINI_MODEL
        self.temperature = settings.preprocessing.GEMINI_TEMPERATURE
        self.max_output_tokens = settings.preprocessing.GEMINI_MAX_OUTPUT_TOKENS

        # Rate limiting config
        self.rpm = settings.preprocessing.GEMINI_RPM
        self.min_delay = 60.0 / self.rpm  # Seconds between requests
        self.last_request_time = 0

        print(f"[GEMINI] Initialized with model: {self.model_name}")
        print(f"[GEMINI] Rate limit: {self.rpm} RPM ({self.min_delay:.1f}s delay)")

    def fix_markdown(self, markdown_text: str) -> str:
        """
        Fix markdown structure using Gemini.

        Args:
            markdown_text: Deformed markdown from LlamaParse/Crawl4AI

        Returns:
            Clean markdown with correct hierarchy

        Raises:
            Exception: If Gemini API call fails
        """
        # Rate limiting
        self._rate_limit()

        # Build prompt
        prompt = self.PROMPT_TEMPLATE.format(markdown=markdown_text)

        # Call Gemini (NEW API)
        try:


            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                )
            )

            # Extract text
            if not response.text:
                raise ValueError("Empty response from Gemini")

            return response.text.strip()

        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

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
