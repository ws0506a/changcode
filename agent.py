"""
Agent 核心循环 - 规划、执行、验证
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from llm import BaseLLM, LLMResponse, ToolCall, create_llm
from tools import ToolSystem, ToolResult
from config import LLMConfig, AgentConfig, ChangCodeConfig


@dataclass
class AgentState:
    """Agent 状态"""
    messages: List[Dict[str, Any]]
    iterations: int = 0
    total_tokens: int = 0
    tool_calls_count: int = 0


class Agent:
    """Agent 核心"""

    def __init__(self, config: ChangCodeConfig):
        self.config = config
        self.llm = create_llm(config.llm)
        self.tool_system = ToolSystem(config.tools)
        self.state = AgentState(messages=[])
        self._setup_system_prompt()

    def _setup_system_prompt(self):
        """设置系统提示"""
        system_prompt = """你是一个专业的AI编程助手，名叫QingCode。

你的能力：
1. 读取和理解代码库
2. 编写和修改代码
3. 执行Shell命令
4. 搜索文件和内容
5. 调试和修复问题

工作原则：
- 先理解需求，再动手
- 读取相关文件，了解上下文
- 逐步完成任务，每步验证
- 遇到问题主动调试
- 保持代码风格一致

工具使用：
- 使用 read_file 读取文件内容
- 使用 write_file 创建新文件
- 使用 edit_file 修改现有文件
- 使用 run_command 执行命令
- 使用 search_files 搜索文件
- 使用 search_content 搜索代码内容

重要：
- 修改文件前先读取，了解现有内容
- 执行危险命令前先确认
- 完成任务后运行测试验证
- 用中文回复用户"""

        self.state.messages.append({
            "role": "system",
            "content": system_prompt
        })

    def chat(self, user_message: str, callback=None) -> str:
        """处理用户消息"""
        # 添加用户消息
        self.state.messages.append({
            "role": "user",
            "content": user_message
        })

        # Agent 循环
        max_iterations = self.config.agent.max_iterations
        
        for i in range(max_iterations):
            self.state.iterations += 1

            # 调用 LLM
            if callback:
                callback("thinking", f"思考中... (第{i+1}轮)")

            response = self.llm.chat(
                messages=self.state.messages,
                tools=self.tool_system.get_openai_tools()
            )

            # 如果有最终回答
            if not response.has_tool_calls:
                # 添加助手消息
                self.state.messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                return response.content

            # 处理工具调用
            # 先添加助手消息（包含工具调用）
            assistant_msg = {
                "role": "assistant",
                "content": response.content or ""
            }

            # OpenAI 格式的工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                assistant_msg["tool_calls"] = []
                for tc in response.tool_calls:
                    assistant_msg["tool_calls"].append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments)
                        }
                    })

            self.state.messages.append(assistant_msg)

            # 执行工具调用
            for tool_call in response.tool_calls:
                self.state.tool_calls_count += 1

                # 检查是否需要确认
                if self.tool_system.needs_confirmation(tool_call.name):
                    if callback:
                        should_continue = callback("confirm", {
                            "tool": tool_call.name,
                            "args": tool_call.arguments
                        })
                        if not should_continue:
                            # 用户取消
                            self.state.messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": "用户取消了操作"
                            })
                            continue

                # 执行工具
                if callback:
                    callback("tool_start", {
                        "tool": tool_call.name,
                        "args": tool_call.arguments
                    })

                result = self.tool_system.execute(tool_call.name, tool_call.arguments)

                if callback:
                    callback("tool_end", {
                        "tool": tool_call.name,
                        "success": result.success,
                        "output": result.output[:500] if result.output else result.error
                    })

                # 添加工具结果
                self.state.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

        # 达到最大迭代次数
        return "达到最大迭代次数，任务可能未完成。请检查结果或继续提问。"

    def reset(self):
        """重置 Agent"""
        self.state = AgentState(messages=[])
        self._setup_system_prompt()

    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.state.messages

    def load_history(self, messages: List[Dict]):
        """加载对话历史"""
        self.state.messages = messages
