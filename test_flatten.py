#!/usr/bin/env python3
"""Test script to debug table flattening - direct LLM call"""

import os
from pathlib import Path
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / "apps" / "knowledge-builder" / ".env"
load_dotenv(env_path)
print(f"Loaded .env from: {env_path}")
print(f"API key set: {bool(os.getenv('OPENAI_API_KEY'))}\n")

# Test with file 547
input_file = Path("data/stages/regulation/547-qd-dhcntt_1-6-23_ban_hanh_chinh_sach_ho_tro_cong_bo_khoa_hoc_danh_cho_sv_cao_hoc_ncs/05-fixed.md")
print(f"Testing with: {input_file}")
print(f"File exists: {input_file.exists()}")

if not input_file.exists():
    print("ERROR: File not found!")
    import sys
    sys.exit(1)

# Read content
content = input_file.read_text(encoding="utf-8")
print(f"\nInput content: {len(content)} chars")
print(f"Has <table> tags: {content.count('<table>')}")
print(f"Has pipe chars: {content.count('|')}")

# Show sample table
if "<table>" in content:
    table_start = content.find("<table>")
    print(f"\nFirst table at char {table_start}:")
    print(content[table_start:table_start+500])

# Create LLM
print("\n\nCreating LLM (gpt-5-mini) with 30min timeout...")
llm = OpenAI(
    model="gpt-5-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=1800.0,  # 30 minutes for long documents
)

# Build prompt (same as in flatten_table_stage.py)
prompt = f"""Bạn là chuyên gia xử lý văn bản học thuật.

NHIỆM VỤ:
1. Tìm TẤT CẢ các bảng trong văn bản (bảng có thể ở dạng Markdown hoặc HTML)
2. Chuyển đổi mỗi bảng thành văn bản mô tả chi tiết, rõ ràng
3. Giữ nguyên HOÀN TOÀN phần văn bản không phải bảng

QUY TẮC CHUYỂN ĐỔI BẢNG:
- Mỗi dòng trong bảng → Viết thành 1 câu văn hoàn chỉnh
- Kết hợp tiêu đề cột và tiêu đề hàng để tạo câu có nghĩa
- Giữ nguyên MỌI con số, ký hiệu, đơn vị (rất quan trọng!)
- Sử dụng ngôn ngữ tự nhiên, dễ đọc, dễ hiểu
- Nếu bảng có nhiều dòng, dùng bullet points hoặc đánh số

QUAN TRỌNG - BẢNG PHỨC TẠP:
- Với bảng HTML có rowspan/colspan (merge cells): ĐỌC KỸ cấu trúc, hiểu đúng ý nghĩa trước khi chuyển đổi
- Với bảng có multi-level headers: Kết hợp tất cả levels để tạo câu đầy đủ ý nghĩa
- Nếu bảng quá phức tạp, ĐƯỢC PHÉP phá quy tắc - miễn sao NỘI DUNG PHẢI ĐÚNG và đầy đủ
- Ưu tiên độ chính xác hơn là format đẹp

VÍ DỤ 1 - Bảng Markdown đơn giản:
Input:
| Hệ đào tạo | TOEIC Nghe-Đọc | TOEIC Nói-Viết |
|------------|----------------|----------------|
| CTC        | 450            | 185            |
| CTTN       | 550            | 205            |

Output:
Yêu cầu chứng chỉ ngoại ngữ:
- Đối với sinh viên Chương trình chuẩn (CTC): TOEIC kỹ năng Nghe-Đọc tối thiểu 450 điểm, kỹ năng Nói-Viết tối thiểu 185 điểm.
- Đối với sinh viên Chương trình tài năng (CTTN): TOEIC kỹ năng Nghe-Đọc tối thiểu 550 điểm, kỹ năng Nói-Viết tối thiểu 205 điểm.

VÍ DỤ 2 - Bảng HTML với rowspan/colspan (phức tạp):
Input:
<table>
<tr>
  <th rowspan="2">Chương trình</th>
  <th colspan="2">Điểm chuẩn</th>
</tr>
<tr>
  <th>Toán</th>
  <th>Tin</th>
</tr>
<tr>
  <td>CNTT Chuẩn</td>
  <td>7.0</td>
  <td>8.0</td>
</tr>
<tr>
  <td>CNTT Tài năng</td>
  <td>8.5</td>
  <td>9.0</td>
</tr>
</table>

Output:
Điểm chuẩn các chương trình:
- Chương trình CNTT Chuẩn: Toán 7.0 điểm, Tin 8.0 điểm
- Chương trình CNTT Tài năng: Toán 8.5 điểm, Tin 9.0 điểm

LƯU Ý:
- Bảng có thể ở dạng Markdown (|...|) hoặc HTML (<table>...</table>) - cả hai đều cần chuyển đổi
- Nếu KHÔNG có bảng nào trong văn bản, trả về văn bản gốc y nguyên
- Không thêm, bớt, hoặc sửa đổi nội dung văn bản gốc
- Chỉ chuyển đổi phần bảng

VĂN BẢN CẦN XỬ LÝ:
{content}

VĂN BẢN ĐÃ CHUYỂN ĐỔI (chỉ trả về văn bản, không giải thích):"""

print(f"\nPrompt length: {len(prompt)} chars")
print("\nCalling LLM...")

response = llm.complete(prompt)
flattened = response.text.strip()

print(f"\nResponse length: {len(flattened)} chars")
print(f"Response has <table> tags: {flattened.count('<table>')}")
print(f"Response has pipe chars: {flattened.count('|')}")
print(f"\nIs same as input: {flattened == content}")

# Save output for inspection
output_file = Path("test_flatten_output.md")
output_file.write_text(flattened, encoding="utf-8")
print(f"\nSaved output to: {output_file}")

if flattened != content:
    print("\n✓ Content was modified by LLM!")
    # Find first difference
    for i, (c1, c2) in enumerate(zip(content, flattened)):
        if c1 != c2:
            print(f"\nFirst diff at char {i}:")
            print(f"  Input:  '{content[max(0,i-20):i+50]}'")
            print(f"  Output: '{flattened[max(0,i-20):i+50]}'")
            break
else:
    print("\n✗ LLM returned EXACT SAME content - something is wrong!")
