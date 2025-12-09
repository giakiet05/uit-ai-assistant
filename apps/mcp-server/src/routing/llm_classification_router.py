"""
LLM Classification Router - Uses LLM to classify query intent and route accordingly.

This strategy uses a fast LLM (e.g., gpt-4o-mini) to classify the user's query
and route to the most relevant collection(s).

Advantages:
- Can handle semantic intent without keywords
- More efficient than query_all for large collection counts
- Adapts to natural language variations

Disadvantages:
- Adds LLM inference latency
- Risk of misclassification
- Requires API calls and costs

Use this strategy when:
- Collection count is large (5+ collections)
- Query latency is less critical
- Cost of querying all collections is high
"""

from typing import List
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI

from ..config.settings import settings
from .base_router import BaseQueryRouter, RoutingDecision


class LLMClassificationRouter(BaseQueryRouter):
    """
    Routes queries using LLM-based classification.

    Uses a fast LLM to understand query intent and select relevant collections.
    """

    # Collection descriptions for classification prompt
    COLLECTION_DESCRIPTIONS = {
        "regulation": "Quy định, quy chế, quyết định, quy trình, hướng dẫn về chính sách và quản lý",
        "curriculum": "Chương trình đào tạo, danh mục môn học, nội dung học phần, kế hoạch đào tạo",
        "announcement": "Thông báo về lịch thi, lịch học, kết quả thi, sự kiện",
    }

    def __init__(self, available_collections: List[str]):
        """
        Initialize LLM classification router.

        Args:
            available_collections: List of collection names that can be queried
        """
        super().__init__(available_collections)

        # Initialize LLM (use fast, cheap model for classification)
        self.llm = OpenAI(
            model=settings.query_routing.CLASSIFICATION_MODEL,
            api_key=settings.credentials.OPENAI_API_KEY,
            temperature=settings.query_routing.CLASSIFICATION_TEMPERATURE
        )

    def route(self, query: str) -> RoutingDecision:
        """
        Route query using LLM classification.

        Args:
            query: User query string

        Returns:
            RoutingDecision with selected collections and reasoning

        Example:
            >>> router = LLMClassificationRouter(["regulation", "curriculum"])
            >>> decision = router.route("UIT có bao nhiêu loại học phần?")
            >>> print(decision.collections)
            ["regulation"]
            >>> print(decision.reasoning)
            "LLM classified query as 'regulation' based on policy/regulation intent"
        """
        # Build classification prompt
        prompt = self._build_classification_prompt(query)

        # Get LLM classification
        try:
            messages = [ChatMessage(role="user", content=prompt)]
            response = self.llm.chat(messages)
            classification = response.message.content.strip().lower()

            # Parse classification result
            selected_collections = self._parse_classification(classification)

            return RoutingDecision(
                collections=selected_collections,
                strategy="llm_classification",
                reasoning=f"LLM classified query as: {classification}"
            )

        except Exception as e:
            # Fallback to query_all on error
            print(f"[WARNING] LLM classification failed: {e}. Falling back to query_all.")
            return RoutingDecision(
                collections=self.available_collections,
                strategy="llm_classification_fallback",
                reasoning=f"LLM error, querying all collections. Error: {str(e)[:50]}"
            )

    def _build_classification_prompt(self, query: str) -> str:
        """
        Build classification prompt for LLM.

        Args:
            query: User query

        Returns:
            Formatted prompt string
        """
        # Build collection options text
        options_text = "\n".join([
            f"- {coll}: {self.COLLECTION_DESCRIPTIONS.get(coll, 'No description')}"
            for coll in self.available_collections
        ])

        prompt = f"""Phân loại câu hỏi vào collection phù hợp.

Collections:
{options_text}

Câu hỏi: "{query}"

### NGUYÊN TẮC PHÂN LOẠI

Hãy trả lời câu hỏi: Người dùng đang hỏi về NGÀNH/CHƯƠNG TRÌNH ĐÀO TẠO CỤ THỂ hay CHÍNH SÁCH CHUNG của trường?

#### BƯỚC 1: Kiểm tra xem câu hỏi có đề cập đến NGÀNH CỤ THỂ không?

PHÂN BIỆT TÊN TRƯỜNG vs TÊN NGÀNH:
- "Trường/Đại học Công nghệ Thông tin" = Tên TRƯỜNG (UIT) -> KHÔNG PHẢI ngành cụ thể
- "Ngành Công nghệ Thông tin" = Tên NGÀNH -> LÀ ngành cụ thể
- "UIT", "ĐHCNTT", "trường" -> chỉ nơi học, KHÔNG phải ngành cụ thể

Tín hiệu về NGÀNH CỤ THỂ (chỉ khi có ít nhất 1 trong các điều sau):
- Có từ khóa: "ngành X", "chuyên ngành X", "chương trình đào tạo X", "CTĐT X"
- Có viết tắt ngành: CNTT, KHMT, KTPM, AI, TTNT, ATTT, KHĐL, MMT&TT, v.v.
- Có tên ngành ĐẦY ĐỦ:
  - "Công nghệ thông tin" (KHI đi cùng "ngành" hoặc viết tắt CNTT)
  - "Khoa học máy tính"
  - "Kỹ thuật phần mềm"
  - "Trí tuệ nhân tạo"
  - "An toàn thông tin"
  - "Khoa học dữ liệu"
  - "Mạng máy tính và Truyền thông dữ liệu"
  - "Kỹ thuật máy tính"
  - "Hệ thống thông tin"
  - "Thương mại điện tử"
  - "Công nghệ kỹ thuật điện tử - truyền thông"

Nếu CÓ tín hiệu ngành cụ thể -> Đi tiếp BƯỚC 2
Nếu KHÔNG (chỉ có tên trường hoặc hỏi chung chung) -> regulation (trả lời ngay, không cần đọc tiếp)

#### BƯỚC 2: Kiểm tra xem có phải chủ đề về chính sách/tài chính không?

Các chủ đề sau LUÔN là regulation (bất kể có nhắc ngành hay không):
- Học phí, chi phí, lệ phí, miễn giảm
- Học bổng, hỗ trợ tài chính
- Quy chế, quy định, quyết định chung của trường
- Thủ tục hành chính: nhập học, chuyển trường, bảo lưu, thôi học

Nếu là chủ đề trên -> regulation
Nếu KHÔNG -> curriculum

### VÍ DỤ

#### Các câu hỏi về NGÀNH CỤ THỂ (có tên ngành/viết tắt ngành)

CÓ ngành CỤ THỂ + KHÔNG phải chính sách/tài chính -> curriculum:
- "Điều kiện tốt nghiệp ngành KTPM 2025" -> curriculum
- "Ngành AI học những môn gì?" -> curriculum
- "Môn học bắt buộc của CNTT" -> curriculum
- "Số tín chỉ tốt nghiệp ngành Khoa học máy tính" -> curriculum
- "CTĐT ngành ATTT năm 2024" -> curriculum

CÓ ngành CỤ THỂ + CÓ chính sách/tài chính -> regulation:
- "Học phí ngành CNTT 2024" -> regulation (chủ đề học phí)
- "Học bổng cho sinh viên ngành AI" -> regulation (chủ đề học bổng)
- "Quy định chuyển ngành sang KTPM" -> regulation (chủ đề quy định/thủ tục)

#### Các câu hỏi CHUNG (không nhắc ngành cụ thể)

Tất cả đều -> regulation:
- "Điều kiện tốt nghiệp của UIT là gì?" -> regulation (chỉ có tên trường, không có ngành)
- "Sinh viên cần bao nhiêu tín chỉ?" -> regulation (hỏi chung)
- "Học phí năm 2024" -> regulation (hỏi chung)
- "Quy chế đào tạo" -> regulation (quy chế chung)
- "Thủ tục bảo lưu" -> regulation (thủ tục hành chính)
- "Trường Đại học Công nghệ Thông tin có bao nhiêu tín chỉ?" -> regulation (tên TRƯỜNG, không phải ngành)
- "UIT yêu cầu điều kiện gì để tốt nghiệp?" -> regulation (tên TRƯỜNG, không có ngành cụ thể)

### LƯU Ý QUAN TRỌNG

1. PHÂN BIỆT KỸ: "Trường/Đại học Công nghệ Thông tin" là TÊN TRƯỜNG (UIT), KHÔNG phải tên ngành!
   - Nếu chỉ có "UIT", "trường", "Đại học Công nghệ Thông tin" -> regulation
   - Nếu có "ngành CNTT", "ngành Công nghệ thông tin", "CNTT" -> curriculum (nếu không phải học phí/quy chế)

2. Chỉ cần có TÊN NGÀNH/VIẾT TẮT NGÀNH + không phải học phí/học bổng/quy chế -> curriculum

3. Không cần từ "chương trình đào tạo" mới là curriculum. Chỉ cần có tên ngành là đủ.

4. Nếu nghi ngờ, hãy tự hỏi: "Câu hỏi này tìm được câu trả lời ở tài liệu chương trình đào tạo của NGÀNH CỤ THỂ, hay ở văn bản quy định CHUNG của trường?"

Trả về: Chỉ ghi TÊN COLLECTION (regulation hoặc curriculum hoặc announcement), không giải thích.

Phân loại:"""

        return prompt

    def _parse_classification(self, classification: str) -> List[str]:
        """
        Parse LLM classification result into collection list.

        Args:
            classification: LLM response string

        Returns:
            List of collection names to query
        """
        classification = classification.lower().strip()

        # Handle "all" case
        if "all" in classification:
            return self.available_collections

        # Parse comma-separated collections
        selected = []
        for coll in self.available_collections:
            if coll in classification:
                selected.append(coll)

        # If no matches, default to all
        if not selected:
            print(f"[WARNING] Could not parse classification '{classification}', using all collections")
            return self.available_collections

        return selected
