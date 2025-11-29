"""
Test curriculum markdown fixer với file thật.

Usage:
    python test/test_curriculum_fixer.py
"""

from pathlib import Path
from src.processing.llm_markdown_fixer import MarkdownFixer


# Curriculum-specific prompt (Vietnamese)
CURRICULUM_PROMPT = """
Bạn là chuyên gia xử lý văn bản chương trình đào tạo của trường đại học.

# NHIỆM VỤ
Sửa lại cấu trúc markdown của văn bản chương trình đào tạo (curriculum) để loại bỏ các lỗi rõ ràng.

**QUAN TRỌNG:**
- KHÔNG tự ý tạo hierarchy mới (vì mỗi khoa có format riêng)
- CHỈ SỬA những lỗi cấu trúc RÕ RÀNG
- GIỮ NGUYÊN nội dung, numbering, và logic tổ chức của văn bản gốc

# CÁC LỖI CẦN SỬA

## 1. Link text đúng ra là header
**Pattern:** Link text có dạng `[1. TÊN SECTION](url)` hoặc `[2. TÊN SECTION](url)`

**Ví dụ:**
```
Input:
[1. GIỚI THIỆU CHUNG](https://daa.uit.edu.vn/...)
## 1.1 Thông tin chung

Output:
# 1. GIỚI THIỆU CHUNG
## 1.1 Thông tin chung
```

```
Input:
[3. CHƯƠNG TRÌNH ĐÀO TẠO](https://daa.uit.edu.vn/...)
## 3.1 Khối lượng kiến thức

Output:
# 3. CHƯƠNG TRÌNH ĐÀO TẠO
## 3.1 Khối lượng kiến thức
```

**Rule:**
- Sections lớn (1, 2, 3, 4, 5) → `#` (Level 1)
- Subsections (1.1, 3.2, 4.5) → `##` (Level 2)
- Sub-subsections (3.3.1, 3.5.2) → `###` (Level 3)

## 2. Bold text đúng ra là subheader
**Pattern:** Text bôi đen `**Về XXX:**` hoặc `**Nhóm XXX**` mà đúng ra là subheader

**Ví dụ 1:**
```
Input:
**Về nhận thức:**
‒ LO1: Nắm vững kiến thức...
‒ LO2: Nắm vững kiến thức...
**Về kỹ năng:**
‒ LO3: Khảo sát tài liệu...

Output:
### Về nhận thức
‒ LO1: Nắm vững kiến thức...
‒ LO2: Nắm vững kiến thức...
### Về kỹ năng
‒ LO3: Khảo sát tài liệu...
```

**Ví dụ 2:**
```
Input:
## 3.3 Khối kiến thức giáo dục chuyên nghiệp
**Nhóm các môn học cơ sở ngành**
- Bắt buộc đối với tất cả sinh viên

Output:
## 3.3 Khối kiến thức giáo dục chuyên nghiệp
### Nhóm các môn học cơ sở ngành
- Bắt buộc đối với tất cả sinh viên
```

**Rule:**
- Nếu bold text là tiêu đề subsection → Chuyển thành `###`
- Nếu bold text chỉ để nhấn mạnh trong đoạn văn → Giữ nguyên bold

## 3. Header levels không nhất quán
**Pattern:** Sequence như `#I` → `## II` → `### III` (không consistent)

**Ví dụ:**
```
Input:
# I. PHẦN THỨ NHẤT
## II. PHẦN THỨ HAI
### III. PHẦN THỨ BA

Output:
# I. PHẦN THỨ NHẤT
# II. PHẦN THỨ HAI
# III. PHẦN THỨ BA
```

**Rule:**
- Nếu thấy pattern I, II, III, IV, V → Normalize về cùng level
- Nếu thấy pattern 1.1, 1.2, 1.3 → Normalize về cùng level

## 4. Bảng bị parse sai
**Pattern:** Bảng có header phức tạp (merged cells) bị tách thành nhiều rows, hoặc data rows thiếu cells

**CRITICAL - QUY TẮC ĐẾMM SEPARATORS:**

Markdown table sử dụng `|` để tách các cells. Số lượng `|` separators quyết định số cột.

**Công thức:**
- Nếu header có **N separators** `|` → Mỗi data row PHẢI có **đúng N separators** `|`
- Ví dụ: `A | B | C` có 2 separators → `1 | 2 | 3` phải có 2 separators

**Cách đếm separators:**
```
STT | Mã | Tên | TC | LT | TH
 ^1  ^2  ^3   ^4  ^5  (5 separators)

1 | SS003 | Tư tưởng | 2 | 2 | 0
^1  ^2     ^3        ^4 ^5  (5 separators) ✅ ĐÚNG!

Lý luận | 13 |
^1         ^2  (only 2 separators) ❌ SAI! Thiếu 3 separators!
```

**Cách fix khi thiếu separators:**
1. Đếm separators trong header: N
2. Đếm separators trong data row: M
3. Nếu M < N → Thêm (N - M) empty cells: `| | |`

**Ví dụ fix:**
```
Input (SAI):
STT | Mã | Tên | TC | LT | TH    ← 5 separators
Lý luận | 13 |                     ← 2 separators (THIẾU 3!)

Output (ĐÚNG):
STT | Mã | Tên | TC | LT | TH    ← 5 separators
Lý luận | 13 | | | |              ← 5 separators (đã thêm 3 empty cells)
```

**LƯU Ý:**
- Empty cell vẫn cần separator: `| |` (không phải `||`)
- Cell cuối cùng có thể có hoặc không có `|` ở cuối (tuỳ style), nhưng **ĐỀ NGHỊ CÓ** để dễ đếm
- **CRITICAL:** Bảng PHẢI có 1 blank line phía trước để render đúng!

**Ví dụ spacing:**
```
SAI (không có blank line):
## Section
Đoạn văn bản...
**Header** | **Column**    ← Sát liền đoạn văn
---|---

ĐÚNG (có blank line):
## Section
Đoạn văn bản...
                          ← BLANK LINE
**Header** | **Column**
---|---
```

---

### **Ví dụ 1: Header bị split (merged cells) - FIX SEPARATORS**

**Input (SAI):**
```
**TT** | **Các khối kiến thức** | **Chương trình đào tạo ngành thứ nhất** | **Chương trình đào tạo song ngành (CTĐT 2)**
       ^1                      ^2                                      ^3  (3 separators)
---|---|---|---
**Cùng nhóm ngành** | **Khác nhóm ngành**
**STC** | **%** | **STC** | **%** | **STC** | **%**
        ^1      ^2        ^3      ^4        ^5  (5 separators)
I | Khối kiến thức giáo dục đại cương | 45 | 36.0 | X | | X |
  ^1                                   ^2  ^3     ^4 ^5^6  (6 separators - SAI!)
II | Khối kiến thức cơ sở ngành | 35 | 28.0 | X* | | 35 | 44.8
   ^1                           ^2  ^3     ^4  ^5^6   ^7  (7 separators - SAI!)
```

**Vấn đề:**
- Header bị split thành 3 rows với số separators khác nhau (3, 5)
- Data rows có 6-7 separators → KHÔNG KHỚP với header!
- Thực tế data có 8 cột (TT, Khối KT, STC_1, %_1, STC_2, %_2, STC_3, %_3)

**Output (ĐÚNG):**
```
**TT** | **Các khối kiến thức** | **CTĐT ngành 1 (STC)** | **CTĐT ngành 1 (%)** | **CTĐT 2 - Cùng nhóm (STC)** | **CTĐT 2 - Cùng nhóm (%)** | **CTĐT 2 - Khác nhóm (STC)** | **CTĐT 2 - Khác nhóm (%)**
      ^1                      ^2                       ^3                       ^4                             ^5                            ^6                             ^7  (7 separators)
---|---|---|---|---|---|---|---
I | Khối kiến thức giáo dục đại cương | 45 | 36.0 | X | | X |
  ^1                                   ^2  ^3     ^4 ^5^6  ^7  (7 separators ✅)
II | Khối kiến thức cơ sở ngành | 35 | 28.0 | X* | | 35 | 44.8
   ^1                           ^2  ^3     ^4  ^5^6   ^7  (7 separators ✅)
```

**Giải thích fix:**
1. **Flatten header:** Merge 3 rows thành 1 row với 8 cột = 7 separators
2. **Check row I:** Đếm separators = 6 → THIẾU 1! → Thêm 1 empty cell cuối
3. **Check row II:** Đếm separators = 7 → ✅ ĐÚNG!
4. **Kết quả:** TẤT CẢ rows có đúng 7 separators

---

### **Ví dụ 2: Row thiếu separators - GROUP HEADER**

**Input (SAI):**
```
**STT** | **Mã môn học** | **Tên môn học** | **TC** | **LT** | **TH**
       ^1             ^2               ^3      ^4      ^5  (5 separators)
---|---|---|---|---|---
**Lý luận chính trị - Pháp luật** | **13** |
                                  ^1       ^2  (only 2 separators - THIẾU 3!)
1 | SS003 | Tư tưởng Hồ Chí Minh | 2 | 2 | 0
  ^1      ^2                      ^3 ^4 ^5  (5 separators ✅)
```

**Vấn đề:**
- Header có 5 separators
- Row "Lý luận chính trị" chỉ có 2 separators → THIẾU 3!
- Đây là row "group header" (nhóm môn học), nên chỉ fill 2 cells đầu

**Output (ĐÚNG):**
```
**STT** | **Mã môn học** | **Tên môn học** | **TC** | **LT** | **TH**
       ^1             ^2               ^3      ^4      ^5  (5 separators)
---|---|---|---|---|---
**Lý luận chính trị - Pháp luật** | **13** | | | |
                                  ^1       ^2^3^4^5  (5 separators ✅)
1 | SS003 | Tư tưởng Hồ Chí Minh | 2 | 2 | 0
  ^1      ^2                      ^3 ^4 ^5  (5 separators ✅)
```

**Giải thích fix:**
1. **Đếm header separators:** 5
2. **Đếm row separators:** 2 → THIẾU 3!
3. **Fix:** Thêm 3 empty cells `| | |` vào cuối row
4. **Kết quả:** Row có đủ 5 separators (khớp với header)

---

### **Ví dụ 3: Nested headers - Flatten và count separators**

**Input (SAI):**
```
**STT** | **Mã MH** | **Tên môn học (MH)** | **Loại MH (bắt buộc/ tự chọn)** | **Tín chỉ**
       ^1         ^2                     ^3                               ^4  (4 separators)
---|---|---|---|---
**Tổng cộng** | **Lý thuyết** | **Thực hành**
             ^1             ^2  (2 separators - nested row, CONFUSING!)
**I** | **Kiến thức giáo dục đại cương** | | | **45** | |
     ^1                                  ^2^3^4       ^5^6  (6 separators)
1 | SS003 | Tư tưởng Hồ Chí Minh | Bắt buộc | 2 | 2 | 0
  ^1      ^2                      ^3        ^4 ^5 ^6  (6 separators)
```

**Vấn đề:**
- Header bị split thành 2 rows (4 sep + 2 sep)
- Data rows có 6 separators → Thực tế có 7 cột!
- Cột "Tín chỉ" nested thành 3 sub-columns → Cần flatten

**Output (ĐÚNG):**
```
**STT** | **Mã MH** | **Tên môn học (MH)** | **Loại MH (bắt buộc/ tự chọn)** | **Tín chỉ (Tổng cộng)** | **Tín chỉ (Lý thuyết)** | **Tín chỉ (Thực hành)**
       ^1         ^2                     ^3                               ^4                       ^5                       ^6  (6 separators)
---|---|---|---|---|---|---
**I** | **Kiến thức giáo dục đại cương** | | | **45** | |
     ^1                                  ^2^3^4       ^5^6  (6 separators ✅)
1 | SS003 | Tư tưởng Hồ Chí Minh | Bắt buộc | 2 | 2 | 0
  ^1      ^2                      ^3        ^4 ^5 ^6  (6 separators ✅)
```

**Giải thích fix:**
1. **Flatten nested header:** Merge "Tín chỉ" với sub-columns → 7 cột (6 separators)
2. **Tên cột descriptive:** "Tín chỉ (Tổng cộng)", "Tín chỉ (Lý thuyết)", "Tín chỉ (Thực hành)"
3. **Check data rows:** Cả 2 rows đều có 6 separators ✅
4. **Kết quả:** TẤT CẢ rows có đúng 6 separators

---

### **Ví dụ 4: Row bắt đầu bằng `|` (thiếu cell đầu - merged cell)**

**Input (SAI):**
```
**Ngành đào tạo** | **Ngành đào tạo cùng nhóm ngành**
                 ^1  (1 separator)
---|---
Thương mại điện tử | **Mã ngành: 73401 Kinh doanh** Quản trị kinh doanh Marketing
                   ^1  (1 separator ✅)
| **Mã ngành: 74801 Máy tính** Khoa học máy tính Mạng máy tính
^1  (ROW BẮT ĐẦU BẰNG | - THIẾU CELL ĐẦU!)
| **Mã ngành: 74802 Công nghệ thông tin** Công nghệ thông tin An toàn thông tin
^1  (ROW BẮT ĐẦU BẰNG | - THIẾU CELL ĐẦU!)
```

**Vấn đề:**
- Header có 1 separator → Mỗi row phải có 2 cells
- Row 1 OK: `Thương mại điện tử | ...`
- Row 2, 3 bắt đầu bằng `|` → Cell đầu TRỐNG (merged cell trong Excel)

**Output (ĐÚNG):**
```
**Ngành đào tạo** | **Ngành đào tạo cùng nhóm ngành**
                 ^1  (1 separator)
---|---
Thương mại điện tử | **Mã ngành: 73401 Kinh doanh** Quản trị kinh doanh Marketing
                   ^1  (1 separator ✅)
Thương mại điện tử | **Mã ngành: 74801 Máy tính** Khoa học máy tính Mạng máy tính
                   ^1  (1 separator ✅ - đã fill cell đầu)
Thương mại điện tử | **Mã ngành: 74802 Công nghệ thông tin** Công nghệ thông tin An toàn thông tin
                   ^1  (1 separator ✅ - đã fill cell đầu)
```

**Giải thích fix:**
1. **Detect pattern:** Row bắt đầu bằng `|` → Merged cell
2. **Fill logic:** Copy giá trị từ row trước (row có data ở cell đầu)
3. **Kết quả:** TẤT CẢ rows có đủ separators và không bắt đầu bằng `|`

---

**RULE TỔNG QUÁT - ALGORITHM FIX TABLES:**

**Bước 1: Xác định số separators chuẩn**
- Nếu header KHÔNG bị split (1 row) → Đếm separators trong header row = N
- Nếu header BỊ SPLIT (nhiều rows) → Flatten trước, rồi đếm separators = N

**Bước 2: Validate từng data row**
- Với MỖI row trong table:
  1. Đếm số separators trong row = M
  2. So sánh M vs N:
     - Nếu M == N → ✅ OK, giữ nguyên
     - Nếu M < N → ❌ THIẾU (N - M) cells → Thêm empty cells `| | |` vào cuối
     - Nếu M > N → ⚠️ THỪA (cảnh báo - có thể header sai)

**Bước 3: Fix merged cells (row bắt đầu bằng `|`)**
- Nếu row bắt đầu bằng `|` → Cell đầu bị merged
- Copy giá trị từ row trước (row gần nhất có data ở cell đầu)

**Bước 4: Ensure blank line before table**
- **CRITICAL:** Bảng PHẢI có 1 blank line phía trước
- Check: Dòng trước header có phải là blank line không?
- Nếu không → Thêm 1 blank line

**Bước 5: Validate kết quả**
- Check TẤT CẢ rows có đúng N separators
- Không row nào bắt đầu bằng `|`
- Separator line `---|---|---` phải có N dấu `---`
- Có blank line trước mỗi bảng

**VÍ DỤ ALGORITHM:**
```
Input table:
Header: STT | Mã | Tên | TC | LT | TH  → Count = 5 separators
Row 1:  1 | SS003 | Tư tưởng | 2 | 2 | 0  → Count = 5 ✅ OK
Row 2:  Lý luận | 13 |                    → Count = 2 ❌ THIẾU 3!

Fix Row 2:
- N = 5 (from header)
- M = 2 (current row)
- Add (5 - 2) = 3 empty cells: Lý luận | 13 | | | |
- Result: 5 separators ✅

Output:
Row 2:  Lý luận | 13 | | | |  → Count = 5 ✅ FIXED!
```

## 5. Sections có title bị tách
**Pattern:** Title văn bản bị tách thành nhiều headers

**Ví dụ:**
```
Input:
# Chương trình đào tạo song ngành
## ngành Thương mại điện tử
### (Áp dụng từ Khoá 19 - 2024)

Output:
# CHƯƠNG TRÌNH ĐÀO TẠO SONG NGÀNH NGÀNH THƯƠNG MẠI ĐIỆN TỬ (ÁP DỤNG TỪ KHOÁ 19 - 2024)
```

**Rule:**
- Nếu 2-3 headers liên tiếp tạo thành 1 title hoàn chỉnh → Merge thành 1 header
- Viết hoa toàn bộ (UPPERCASE)
- Level: `#` (Level 1)

# QUY TẮC CHUNG

1. **KHÔNG thay đổi nội dung:** Giữ nguyên từ ngữ, văn phong, numbering
2. **KHÔNG thay đổi tables:** Giữ nguyên nội dung bảng, chỉ fix structure nếu sai
3. **KHÔNG tự ý thêm headers:** Chỉ chuyển đổi từ link/bold sang header nếu rõ ràng là lỗi parse
4. **CHỈ SỬA cấu trúc:** Header levels, link → header, bold → header, table structure
5. **Normalize bullet characters:** Chuyển tất cả dấu dash đầu dòng thành `-` (hyphen-minus)

## 6. Bullet list characters không đúng

**Pattern:** Văn bản dùng en dash `‒` (U+2012) hoặc em dash `—` thay vì hyphen `-` (U+002D)

**Ví dụ:**
```
Input (SAI):
‒ LO1: Nắm vững kiến thức...    ← En dash (U+2012) - KHÔNG render thành bullet
‒ LO2: Nắm vững kiến thức...

Output (ĐÚNG):
- LO1: Nắm vững kiến thức...    ← Hyphen (U+002D) - Render thành bullet ✅
- LO2: Nắm vững kiến thức...
```

**Rule:**
- Tìm tất cả dòng bắt đầu bằng `‒` (en dash), `—` (em dash), `–` (other dashes)
- Replace bằng `-` (hyphen-minus U+002D)
- Chỉ replace ở **đầu dòng** (bullet), không replace trong text

# INPUT MARKDOWN
```markdown
{markdown}
```

# OUTPUT
Chỉ output markdown đã sửa, KHÔNG giải thích, KHÔNG thêm bất kỳ text nào khác ngoài markdown.
Markdown phải bắt đầu ngay từ dòng đầu tiên.
"""


def test_curriculum_fixer():
    """Test curriculum fixer với file thật."""

    # Paths
    input_file = Path("data/processed/curriculum/content-chuong-trinh-dao-tao-song-nganh-nganh-thuong-mai-dien-tu-ap-dung-tu-khoa-19-2024.md")
    output_file = Path("test/test_curriculum_fixed.md")

    print(f"Input: {input_file}")
    print(f"Output: {output_file}\n")

    # Read input
    with open(input_file, encoding='utf-8') as f:
        original_markdown = f.read()

    print(f"Original length: {len(original_markdown)} chars\n")

    # Create fixer with default Gemini LLM
    print("Creating MarkdownFixer...")
    fixer = MarkdownFixer()

    # Build custom prompt for curriculum
    print("Building curriculum-specific prompt...")
    prompt = CURRICULUM_PROMPT.format(markdown=original_markdown)

    print(f"Prompt length: {len(prompt)} chars\n")

    # Call LLM directly (bypass default regulation prompt)
    print("Calling Gemini API...")
    print("⚠️  NOTE: This will cost API credits!\n")

    # Rate limit
    #fixer._rate_limit()

    # Call LLM
    try:
        response = fixer.llm.complete(prompt)

        if not response.text:
            raise ValueError("Empty response from LLM")

        fixed_markdown = response.text.strip()

        print(f"✅ Got response: {len(fixed_markdown)} chars\n")

        # Save output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fixed_markdown)

        print(f"✅ Saved to: {output_file}")

        # Stats
        print("\n" + "="*50)
        print("STATISTICS:")
        print(f"Original: {len(original_markdown)} chars, {original_markdown.count('\\n')} lines")
        print(f"Fixed:    {len(fixed_markdown)} chars, {fixed_markdown.count('\\n')} lines")
        print(f"Diff:     {len(fixed_markdown) - len(original_markdown):+d} chars")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    test_curriculum_fixer()
