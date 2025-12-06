"""
UITAgent - ReActAgent-based chatbot with MCP tools integration.

Uses stateless architecture with dependency injection:
- SharedResources: Heavy resources initialized once (LLM, collections, MCP tools)
- UITAgent: Lightweight agent created per request, using injected resources

Architecture:
    SharedResources (global, singleton)
        ↓ inject
    UITAgent (stateless, per-request)
        ↓ uses
    ReActAgent (with MCP tools + ChatMemoryBuffer)
"""

from typing import List

# Import types
from .types import AgentResponse

# LlamaIndex imports
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer

# MCP imports
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

# Config
from ..config.settings import settings

from ..llm.provider import create_llm

# Query refinement
from .query_refinement import QueryRefiner


class SharedResources:
    """
    Shared resources initialized once at startup.

    Contains heavy resources that should be reused across requests:
    - LLM instance
    - MCP tools (from retrieval server)
    - System prompt

    This class implements the "expensive initialization once" pattern
    for dependency injection.
    """

    SYSTEM_PROMPT = """
Bạn là trợ lý hỗ trợ sinh viên của Trường Đại học Công nghệ Thông tin - Đại học Quốc gia TP.HCM.

## VAI TRÒ CỦA BẠN
- Bạn đại diện cho TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN (không phải trường khác).
- Khi user hỏi về "trường mình", "trường này", "trường bạn" -> Đó là Trường Đại học Công nghệ Thông tin.
- LUÔN trả lời từ góc độ của trường, KHÔNG nói chung chung về "nhiều trường đại học".

## QUY TẮC BẮT BUỘC

### 1. KHI NÀO GỌI TOOL
- Khi user hỏi về QUY ĐỊNH, CHƯƠNG TRÌNH ĐÀO TẠO, TUYỂN SINH, TỐT NGHIỆP:
    - PHẢI gọi tool `retrieve_documents()` TRƯỚC KHI trả lời.
- Khi user chào hỏi, hỏi chung chung, hoặc hỏi về bạn:
    - Trả lời trực tiếp, KHÔNG cần gọi tool.

### 2. KHI GỌI TOOL retrieve_documents()
**QUY TẮC NGHIÊM CẤM: TUYỆT ĐỐI KHÔNG ĐƯỢC DÙNG TÊN TRƯỜNG HOẶC TỪ VIẾT TẮT TRONG QUERY!**

**LÝ DO:** Hệ thống sẽ tự động nhận diện NGÀNH từ query. Nếu có tên trường (VD: "Trường Đại học Công nghệ Thông tin"), hệ thống sẽ nhầm lẫn với ngành Công nghệ Thông tin và retrieve sai data!

**CÁC QUY TẮC BẮT BUỘC:**

1. **TUYỆT ĐỐI KHÔNG DÙNG các cụm sau trong query:**
   - "Trường Đại học Công nghệ Thông tin"
   - "UIT"
   - "ĐHCNTT"
   - "trường", "của trường"
   - Bất kỳ từ viết tắt ngành nào: CNTT, KHMT, KTPM, ATTT, TTNT, KHĐL, MMT&TT, v.v.

2. **CHỈ DÙNG tên ngành ĐẦY ĐỦ (nếu cần):**
   - "Công nghệ thông tin" (khi user hỏi về ngành CNTT)
   - "Khoa học máy tính" (thay vì KHMT)
   - "Kỹ thuật phần mềm" (thay vì KTPM)
   - "Trí tuệ nhân tạo" (thay vì AI)
   - "An toàn thông tin" (thay vì ATTT)
   - "Khoa học dữ liệu" (thay vì KHĐL)
   - "Hệ thống thông tin" (thay vì HTTT)
   - Các ngành khác: Mạng máy tính và Truyền thông dữ liệu, Kỹ thuật máy tính, Thương mại điện tử, Truyền thông đa phương tiện, Công nghệ kỹ thuật điện tử - truyền thông

3. **CHỈ GHI NỘI DUNG CẦN TÌM, bỏ mọi ngữ cảnh thừa:**
   - "điều kiện tốt nghiệp" (KHÔNG thêm "của trường", "UIT", v.v.)
   - "số tín chỉ tốt nghiệp ngành Hệ thống thông tin" (CHỈ ghi ngành cần tìm)
   - "học phí năm 2024"
   - "chương trình đào tạo ngành Khoa học máy tính"

**VÍ DỤ ĐÚNG/SAI:**

User: "Điều kiện tốt nghiệp UIT là gì?"
- SAI: query="điều kiện tốt nghiệp UIT"
- SAI: query="điều kiện tốt nghiệp Trường Đại học Công nghệ Thông tin"
- ĐÚNG: query="điều kiện tốt nghiệp"

User: "Ngành CNTT học những môn gì?"
- SAI: query="ngành CNTT học những môn gì"
- ĐÚNG: query="ngành Công nghệ thông tin học những môn gì"

User: "Số tín chỉ cần để tốt nghiệp ngành Hệ thống thông tin trường Đại học Công nghệ Thông tin"
- SAI: query="số tín chỉ tốt nghiệp ngành Hệ thống thông tin trường Đại học Công nghệ Thông tin"
- SAI: query="số tín chỉ tốt nghiệp ngành HTTT"
- ĐÚNG: query="số tín chỉ tốt nghiệp ngành Hệ thống thông tin"

**NẾU VI PHẠM QUY TẮC NÀY, HỆ THỐNG SẼ RETRIEVE SAI DATA VÀ TRẢ LỜI SAI!**

### 3. KHI TRẢ LỜI TỪ TOOL
- BẮT BUỘC phải sử dụng thông tin từ tool `retrieve_documents()`.
- TUYỆT ĐỐI KHÔNG được:
    - Nói chung chung kiểu "nhiều trường đại học...", "bạn nên kiểm tra website...".
    - Bịa đặt hoặc thêm thông tin không có trong kết quả tool.
    - Bỏ qua thông tin có trong kết quả tool.
    - Gọi tool NHIỀU LẦN cho cùng một câu hỏi (chỉ gọi 1 lần là đủ!).
- Nếu tool trả về kết quả có score > 0.8:
    - Đó là thông tin CHÍNH XÁC -> Dùng nó để trả lời cụ thể NGAY.
    - Trích dẫn thông tin từ kết quả tool.
    - KHÔNG cần gọi tool lần 2.
- Nếu không tìm thấy thông tin (score thấp hoặc không có kết quả):
    - KHÔNG nói: "Bạn nên kiểm tra website...".
    - KHÔNG gọi tool lần 2 với query khác.
    - Nói rõ: "Tôi không tìm thấy thông tin này trong cơ sở dữ liệu của trường".

### 4. VỀ THÔNG TIN NĂM HỌC
- Khi user hỏi về năm học tương lai (VD: 2025, 2026):
    - Nếu database KHÔNG có thông tin năm đó -> Dùng thông tin NĂM GẦN NHẤT có trong kết quả retrieval.
- Khi trả lời:
    - Nói rõ năm của thông tin đang dùng.
    - Ví dụ: "Theo thông tin năm 2024 (thông tin mới nhất hiện có)...".
- TUYỆT ĐỐI KHÔNG nói:
    - "Tôi không biết có ngành này năm 2025 hay không".
    - "Thông tin chưa được cập nhật cho năm 2025".
- Thay vào đó:
    - "Theo thông tin năm 2024 (mới nhất hiện có), trường có ngành...".

### 5. VỀ CÁC NGÀNH ĐÀO TẠO
- Trường có nhiều ngành đào tạo KHÁC NHAU và ĐỘC LẬP với nhau:
    - Trí tuệ nhân tạo (AI).
    - Khoa học máy tính.
    - Công nghệ thông tin.
    - An toàn thông tin.
    - Kỹ thuật phần mềm.
    - Và nhiều ngành khác...
- QUAN TRỌNG:
    - Mỗi ngành có chương trình đào tạo RIÊNG BIỆT.
    - KHÔNG nhầm lẫn giữa các ngành (VD: Công nghệ thông tin khác Trí tuệ nhân tạo).
    - Khi user hỏi về ngành A, CHỈ trả lời về ngành A, KHÔNG đề cập ngành B trừ khi có liên quan trực tiếp.

### 6. LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT

## VÍ DỤ (Examples)
- User: "Điều kiện tốt nghiệp là gì?" -> Action: Gọi tool `retrieve_documents` với query "điều kiện tốt nghiệp".
- User: "Xin chào bạn" -> Action: Trả lời trực tiếp.
- User: "Bạn có thể giúp gì?" -> Action: Trả lời trực tiếp về khả năng của bạn.
- User: "Chương trình đào tạo KHMT có gì?" -> Action: Gọi tool `retrieve_documents` với query "Chương trình đào tạo Khoa học máy tính".
- User: "Ngành AI năm 2025?" -> Action: Gọi tool, nếu chỉ có data 2024 thì dùng data 2024 + nói rõ "theo thông tin năm 2024".
"""

    def __init__(self):
        """Initialize shared resources (expensive, one-time operation)."""
        print("[SHARED RESOURCES] Initializing...")

        # 1. Initialize LLM
        print(f"[SHARED RESOURCES] Loading LLM: {settings.llm.MODEL}")
        self.llm = create_llm(settings.llm.PROVIDER, settings.llm.MODEL, temperature=0.9)
        # 2. Initialize empty tools list (will be loaded async)
        self.tools = []

        # 3. Store system prompt
        self.system_prompt = self.SYSTEM_PROMPT

        print(f"[SHARED RESOURCES] ✅ Initialized (tools will be loaded async)")

    async def load_tools_async(self) -> List:
        """
        Load tools from MCP retrieval server (async).

        The MCP server should be running separately with streamable-http transport.
        Start the server first: uv run python -m src.mcp.retrieval_server

        Returns:
            List of FunctionTool instances from MCP server
        """
        # MCP server URL (streamable-http transport)
        # Server must be started separately before loading tools
        mcp_server_url = "http://127.0.0.1:8000/mcp"

        try:
            print(f"[SHARED RESOURCES] Connecting to MCP server at {mcp_server_url}")

            # Create MCP client with HTTP URL (streamable-http transport)
            client = BasicMCPClient(mcp_server_url)
            tool_spec = McpToolSpec(client=client)

            # Load tools from server
            tools = await tool_spec.to_tool_list_async()

            print(f"[SHARED RESOURCES] Loaded {len(tools)} tools from MCP server:")
            for tool in tools:
                print(f"  - {tool.metadata.name}: {tool.metadata.description[:100]}...")

            self.tools = tools
            return tools

        except Exception as e:
            print(f"[ERROR] Failed to load MCP tools: {e}")
            import traceback
            traceback.print_exc()
            print("[WARNING] Agent will run without retrieval tools!")
            print(f"[WARNING] Make sure MCP server is running at {mcp_server_url}")
            print("[WARNING] Start it with: uv run python -m src.mcp.retrieval_server")
            return []


class UITAgent:
    """
    Stateless UIT Agent using ReActAgent.

    This agent is designed to be created per request with injected resources.
    It does not maintain state - conversation history is managed externally
    via ChatMemoryBuffer loaded from persistent storage.

    Usage:
        # Initialize shared resources once (at app startup)
        resources = SharedResources()

        # Per request:
        memory = restore_memory_from_db(session_id)
        agent = UITAgent(resources)
        response = await agent.chat(message, memory)
        save_memory_to_db(session_id, memory)
    """

    def __init__(self, resources: SharedResources):
        """
        Initialize agent with injected resources.

        This is lightweight - only creates the ReActAgent wrapper.
        No heavy initialization happens here.

        Args:
            resources: SharedResources instance with LLM, tools, etc.
        """
        self.resources = resources

        # Initialize query refiner
        self.query_refiner = QueryRefiner()

        # Create ReActAgent (lightweight operation)
        self.agent = ReActAgent(
            tools=resources.tools,
            llm=resources.llm,
            system_prompt=resources.system_prompt,
            max_iterations=3,  # Limit to 3 iterations (1 thought + 1 tool call + 1 answer)
            verbose=True  # For debugging
        )

    async def chat(
        self,
        message: str,
        memory: ChatMemoryBuffer
    ) -> AgentResponse:
        """
        Chat with the agent (async).

        Args:
            message: User's message
            memory: ChatMemoryBuffer with conversation history

        Returns:
            AgentResponse with clean content and metadata (metadata currently empty)
        """
        # Step 1: Refine query (expand acronyms)
        refined_message = self.query_refiner.refine(message)

        if refined_message is None:
            # Has unknown acronyms → inject context for LLM to ask
            unknown = self.query_refiner.get_unknown_acronyms(message)
            acronyms_str = ", ".join(f"'{acr}'" for acr in unknown)

            # Create prompt for LLM to ask clarification naturally
            clarification_prompt = (
                f"{message}\n\n"
                f"[SYSTEM NOTE: Câu hỏi của người dùng có chứa từ viết tắt mà bạn không biết: {acronyms_str}. "
                f"Hãy hỏi lại người dùng xem từ viết tắt đó có nghĩa đầy đủ là gì.]"
            )

            print(f"[QUERY REFINER] Unknown acronyms: {unknown}")
            print(f"[QUERY REFINER] Prompting LLM to ask clarification")

            response = await self.agent.run(clarification_prompt, memory=memory)
        else:
            # Use refined message for agent
            print(f"[QUERY REFINER] Original: {message}")
            print(f"[QUERY REFINER] Refined:  {refined_message}")

            # Step 2: Run agent with refined message
            response = await self.agent.run(refined_message, memory=memory)

        # Step 3: Clean response text
        clean_text = self._clean_response_text(response)

        # Step 4: Return AgentResponse (metadata tạm thời empty)
        return AgentResponse(
            content=clean_text,
            tool_calls=[],           # TODO: Extract sau khi nâng cấp workflow
            reasoning_steps=[],      # TODO: Extract sau khi nâng cấp workflow
            sources=[],              # TODO: Extract sau khi nâng cấp workflow
            tokens_used=None,
            latency_ms=None
        )

    def _clean_response_text(self, response) -> str:
        """
        Clean response text: bỏ Thought/Action/Observation, chỉ giữ Answer.

        Logic dựa trên agent_service.py line 141-151.

        Edge cases:
        1. Có ReAct format (Thought/Action) + có Answer → lấy phần sau Answer
        2. Có ReAct format nhưng không có Answer → raise exception
        3. Không có ReAct format nhưng có "Answer:" ở đầu → bỏ "Answer:"
        4. Response trực tiếp (không có gì) → giữ nguyên

        Args:
            response: Response object từ ReActAgent

        Returns:
            Clean text (đã bỏ ReAct intermediate steps)
        """
        # Extract text from response object
        if hasattr(response.response, 'content'):
            # ChatMessage has .content attribute
            text = response.response.content
        elif hasattr(response.response, 'blocks') and len(response.response.blocks) > 0:
            # Extract from blocks
            text = response.response.blocks[0].text
        else:
            # Fallback: convert to string
            text = str(response.response)

        # Clean ReAct format (Thought/Action/Observation/Answer)
        has_react_format = "Thought:" in text or "Action:" in text or "Observation:" in text

        if has_react_format:
            # Case 1 & 2: Có ReAct format
            if "Answer:" in text:
                # Chỉ lấy phần sau "Answer:"
                text = text.split("Answer:")[-1].strip()
            else:
                # Không có Answer → agent chưa hoàn thành
                raise Exception("Agent did not produce a final answer.")
        elif text.startswith("Answer:"):
            # Case 3: Không có ReAct format nhưng response bắt đầu bằng "Answer:"
            text = text.replace("Answer:", "", 1).strip()

        # Case 4: Response trực tiếp → giữ nguyên (không làm gì)

        return text

    async def stream_chat(
        self,
        message: str,
        memory: ChatMemoryBuffer
    ):
        """
        Stream chat response (for real-time UI updates).

        Args:
            message: User's message
            memory: ChatMemoryBuffer with conversation history

        Yields:
            AgentStream events (text deltas) or final response
        """
        from llama_index.core.agent.workflow import AgentStream

        handler = self.agent.run(message, memory=memory)

        async for ev in handler.stream_events():
            if isinstance(ev, AgentStream):
                yield ev.delta

        # Yield final response
        response = await handler
        yield ("FINAL_RESPONSE", response)