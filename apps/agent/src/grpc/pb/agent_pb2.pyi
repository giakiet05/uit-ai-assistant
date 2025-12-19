from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ToolCall(_message.Message):
    __slots__ = ("tool_name", "args_json", "output")
    TOOL_NAME_FIELD_NUMBER: _ClassVar[int]
    ARGS_JSON_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    tool_name: str
    args_json: str
    output: str
    def __init__(self, tool_name: _Optional[str] = ..., args_json: _Optional[str] = ..., output: _Optional[str] = ...) -> None: ...

class Source(_message.Message):
    __slots__ = ("title", "content", "score", "url")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    title: str
    content: str
    score: float
    url: str
    def __init__(self, title: _Optional[str] = ..., content: _Optional[str] = ..., score: _Optional[float] = ..., url: _Optional[str] = ...) -> None: ...

class ChatRequest(_message.Message):
    __slots__ = ("message", "user_id", "thread_id")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    THREAD_ID_FIELD_NUMBER: _ClassVar[int]
    message: str
    user_id: str
    thread_id: str
    def __init__(self, message: _Optional[str] = ..., user_id: _Optional[str] = ..., thread_id: _Optional[str] = ...) -> None: ...

class ChatResponse(_message.Message):
    __slots__ = ("content", "tool_calls", "reasoning_steps", "sources", "tokens_used", "latency_ms")
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALLS_FIELD_NUMBER: _ClassVar[int]
    REASONING_STEPS_FIELD_NUMBER: _ClassVar[int]
    SOURCES_FIELD_NUMBER: _ClassVar[int]
    TOKENS_USED_FIELD_NUMBER: _ClassVar[int]
    LATENCY_MS_FIELD_NUMBER: _ClassVar[int]
    content: str
    tool_calls: _containers.RepeatedCompositeFieldContainer[ToolCall]
    reasoning_steps: _containers.RepeatedScalarFieldContainer[str]
    sources: _containers.RepeatedCompositeFieldContainer[Source]
    tokens_used: int
    latency_ms: int
    def __init__(self, content: _Optional[str] = ..., tool_calls: _Optional[_Iterable[_Union[ToolCall, _Mapping]]] = ..., reasoning_steps: _Optional[_Iterable[str]] = ..., sources: _Optional[_Iterable[_Union[Source, _Mapping]]] = ..., tokens_used: _Optional[int] = ..., latency_ms: _Optional[int] = ...) -> None: ...
