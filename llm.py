"""
LLM 接口层 - 支持多种模型提供商
"""

import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from config import LLMConfig


class ToolCall:
    """工具调用"""
    def __init__(self, id: str, name: str, arguments: Dict[str, Any]):
        self.id = id
        self.name = name
        self.arguments = arguments

    def __repr__(self):
        return f"ToolCall(name={self.name}, args={self.arguments})"


class LLMResponse:
    """LLM 响应"""
    def __init__(self, content: str, tool_calls: List[ToolCall] = None, raw_response: Any = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.raw_response = raw_response

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def __repr__(self):
        if self.has_tool_calls:
            return f"LLMResponse(tools={[t.name for t in self.tool_calls]})"
        return f"LLMResponse(content={self.content[:50]}...)"


class BaseLLM(ABC):
    """LLM 基类"""

    @abstractmethod
    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> LLMResponse:
        pass


class OpenAILLM(BaseLLM):
    """OpenAI 兼容接口 (支持 DeepSeek, GLM, Qwen 等)"""

    def __init__(self, config: LLMConfig):
        from openai import OpenAI
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> LLMResponse:
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        # 解析工具调用
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            raw_response=response
        )


class AnthropicLLM(BaseLLM):
    """Anthropic Claude 接口"""

    def __init__(self, config: LLMConfig):
        import anthropic
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)

    def chat(self, messages: List[Dict], tools: List[Dict] = None) -> LLMResponse:
        # 转换消息格式
        system_msg = ""
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        kwargs = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": chat_messages,
        }

        if system_msg:
            kwargs["system"] = system_msg

        if tools:
            # 转换工具格式为 Anthropic 格式
            anthropic_tools = []
            for tool in tools:
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
            kwargs["tools"] = anthropic_tools

        response = self.client.messages.create(**kwargs)

        # 解析响应
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw_response=response
        )


def create_llm(config: LLMConfig) -> BaseLLM:
    """创建 LLM 实例"""
    if config.provider == "anthropic":
        return AnthropicLLM(config)
    else:
        return OpenAILLM(config)
